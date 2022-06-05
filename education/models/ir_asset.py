import os

from glob import glob
from logging import getLogger
from werkzeug import urls

import odoo
from odoo.tools import misc
from odoo import tools
from odoo import api, fields, http, models
from odoo.http import root

_logger = getLogger(__name__)

SCRIPT_EXTENSIONS = ('js',)
STYLE_EXTENSIONS = ('css', 'scss', 'sass', 'less')
TEMPLATE_EXTENSIONS = ('xml',)
DEFAULT_SEQUENCE = 16

# Directives are stored in variables for ease of use and syntax checks.
APPEND_DIRECTIVE = 'append'
PREPEND_DIRECTIVE = 'prepend'
AFTER_DIRECTIVE = 'after'
BEFORE_DIRECTIVE = 'before'
REMOVE_DIRECTIVE = 'remove'
REPLACE_DIRECTIVE = 'replace'
INCLUDE_DIRECTIVE = 'include'
# Those are the directives used with a 'target' argument/field.
DIRECTIVES_WITH_TARGET = [AFTER_DIRECTIVE, BEFORE_DIRECTIVE, REPLACE_DIRECTIVE]
WILDCARD_CHARACTERS = {'*', "?", "[", "]"}


def fs2web(path):
    """Converts a file system path to a web path"""
    if os.path.sep == '/':
        return path
    return '/'.join(path.split(os.path.sep))

def can_aggregate(url):
    parsed = urls.url_parse(url)
    return not parsed.scheme and not parsed.netloc and not url.startswith('/web/content')

def is_wildcard_glob(path):
    """Determine whether a path is a wildcarded glob eg: "/web/file[14].*"
    or a genuine single file path "/web/myfile.scss"""
    return not WILDCARD_CHARACTERS.isdisjoint(path)

class Asset(models.Model):
    _inherit = 'ir.asset'

    def _fill_asset_paths(self, bundle, addons, installed, css, js, xml, asset_paths, seen):
        """
        Fills the given AssetPaths instance by applying the operations found in
        the matching bundle of the given addons manifests.
        See `_get_asset_paths` for more information.

        :param bundle: name of the bundle from which to fetch the file paths
        :param addons: list of addon names as strings
        :param css: boolean: whether or not to include style files
        :param js: boolean: whether or not to include script files
        :param xml: boolean: whether or not to include template files
        :param asset_paths: the AssetPath object to fill
        :param seen: a list of bundles already checked to avoid circularity
        """
        if bundle in seen:
            raise Exception("Circular assets bundle declaration: %s" % " > ".join(seen + [bundle]))

        if not root._loaded:
            root.load_addons()
            root._loaded = True
        manifest_cache = http.addons_manifest
        exts = []
        if js:
            exts += SCRIPT_EXTENSIONS
        if css:
            exts += STYLE_EXTENSIONS
        if xml:
            exts += TEMPLATE_EXTENSIONS

        # this index is used for prepending: files are inserted at the beginning
        # of the CURRENT bundle.
        bundle_start_index = len(asset_paths.list)

        def process_path(directive, target, path_def):
            """
            This sub function is meant to take a directive and a set of
            arguments and apply them to the current asset_paths list
            accordingly.

            It is nested inside `_get_asset_paths` since we need the current
            list of addons, extensions, asset_paths and manifest_cache.

            :param directive: string
            :param target: string or None or False
            :param path_def: string
            """
            if directive == INCLUDE_DIRECTIVE:
                # recursively call this function for each INCLUDE_DIRECTIVE directive.
                self._fill_asset_paths(path_def, addons, installed, css, js, xml, asset_paths, seen + [bundle])
                return

            addon, paths = self._get_paths(path_def, installed, exts)

            # retrieve target index when it applies
            if directive in DIRECTIVES_WITH_TARGET:
                _, target_paths = self._get_paths(target, installed, exts)
                if not target_paths and target.rpartition('.')[2] not in exts:
                    # nothing to do: the extension of the target is wrong
                    return
                target_to_index = len(target_paths) and target_paths[0] or target
                target_index = asset_paths.index(target_to_index, addon, bundle)

            if directive == APPEND_DIRECTIVE:
                asset_paths.append(paths, addon, bundle)
            elif directive == PREPEND_DIRECTIVE:
                asset_paths.insert(paths, addon, bundle, bundle_start_index)
            elif directive == AFTER_DIRECTIVE:
                asset_paths.insert(paths, addon, bundle, target_index + 1)
            elif directive == BEFORE_DIRECTIVE:
                asset_paths.insert(paths, addon, bundle, target_index)
            elif directive == REMOVE_DIRECTIVE:
                asset_paths.remove(paths, addon, bundle)
            elif directive == REPLACE_DIRECTIVE:
                asset_paths.insert(paths, addon, bundle, target_index)
                asset_paths.remove(target_paths, addon, bundle)
            #else:
                # this should never happen
                #raise ValueError("Unexpected directive")

        # 1. Process the first sequence of 'ir.asset' records
        assets = self._get_related_assets([('bundle', '=', bundle)]).filtered('active')
        for asset in assets.filtered(lambda a: a.sequence < DEFAULT_SEQUENCE):
            process_path(asset.directive, asset.target, asset.path)

        # 2. Process all addons' manifests.
        for addon in self._topological_sort(tuple(addons)):
            manifest = manifest_cache.get(addon)
            if not manifest:
                continue
            manifest_assets = manifest.get('assets', {})
            for command in manifest_assets.get(bundle, []):
                directive, target, path_def = self._process_command(command)
                process_path(directive, target, path_def)

        # 3. Process the rest of 'ir.asset' records
        for asset in assets.filtered(lambda a: a.sequence >= DEFAULT_SEQUENCE):
            process_path(asset.directive, asset.target, asset.path)

    def _get_paths(self, path_def, installed, extensions=None):
        """
        Returns a list of file paths matching a given glob (path_def) as well as
        the addon targeted by the path definition. If no file matches that glob,
        the path definition is returned as is. This is either because the path is
        not correctly written or because it points to a URL.

        :param path_def: the definition (glob) of file paths to match
        :param installed: the list of installed addons
        :param extensions: a list of extensions that found files must match
        :returns: a tuple: the addon targeted by the path definition [0] and the
            list of file paths matching the definition [1] (or the glob itself if
            none). Note that these paths are filtered on the given `extensions`.
        """
        paths = []
        path_url = fs2web(path_def)
        path_parts = [part for part in path_url.split('/') if part]
        addon = path_parts[0]
        addon_manifest = http.addons_manifest.get(addon)

        safe_path = True
        if addon_manifest:
            #if addon not in installed:
                # Assert that the path is in the installed addons
                #raise Exception("Unallowed to fetch files from addon %s" % addon)
            addons_path = os.path.join(addon_manifest['addons_path'], '')[:-1]
            full_path = os.path.normpath(os.path.join(addons_path, *path_parts))

            # first security layer: forbid escape from the current addon
            # "/mymodule/../myothermodule" is forbidden
            # the condition after the or is to further guarantee that we won't access
            # a directory that happens to be named like an addon (web....)
            if addon not in full_path or addons_path not in full_path:
                addon = None
                safe_path = False
            else:
                paths = [
                    path for path in sorted(glob(full_path, recursive=True))
                ]

            # second security layer: do we have the right to access the files
            # that are grabbed by the glob ?
            # In particular we don't want to expose data in xmls of the module
            def is_safe_path(path):
                try:
                    misc.file_path(path, SCRIPT_EXTENSIONS + STYLE_EXTENSIONS + TEMPLATE_EXTENSIONS)
                except (ValueError, FileNotFoundError):
                    return False
                if path.rpartition('.')[2] in TEMPLATE_EXTENSIONS:
                    # normpath will strip the trailing /, which is why it has to be added afterwards
                    static_path = os.path.normpath("%s/static" % addon) + os.path.sep
                    # Forbid xml to leak
                    return static_path in path
                return True

            len_paths = len(paths)
            paths = list(filter(is_safe_path, paths))
            safe_path = safe_path and len_paths == len(paths)

            # When fetching template file paths, we need the full paths since xml
            # files are read from the file system. But web assets (scripts and
            # stylesheets) must be loaded using relative paths, hence the trimming
            # for non-xml file paths.
            paths = [path if path.split('.')[-1] in TEMPLATE_EXTENSIONS else fs2web(path[len(addons_path):]) for path in paths]

        else:
            addon = None

        if not paths and (not can_aggregate(path_url) or (safe_path and not is_wildcard_glob(path_url))):
            # No file matching the path; the path_def could be a url.
            paths = [path_url]

        if not paths:
            msg = f'IrAsset: the path "{path_def}" did not resolve to anything.'
            if not safe_path:
                msg += " It may be due to security reasons."
            _logger.warning(msg)
        # Paths are filtered on the extensions (if any).
        return addon, [
            path
            for path in paths
            if not extensions or path.split('.')[-1] in extensions
        ]
    