from odoo import api, fields, models
import os
from odoo.exceptions import UserError
import base64


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def _get_path(self, bin_data, sha):
        # retro compatibility
        fname = sha[:3] + '/' + sha
        full_path = self._full_path(fname)
        if os.path.isfile(full_path):
            return fname, full_path  # keep existing path

        # scatter files across 256 dirs
        # we use '/' in the db (even on windows)
        fname = sha[:2] + '/' + sha
        full_path = self._full_path(fname)
        dirname = os.path.dirname(full_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        # prevent sha-1 collision
        if os.path.isfile(full_path) and not self._same_content(bin_data, full_path):
            raise UserError("path is: " + str(full_path))
        return fname, full_path

    def assign_companies_countries(self):
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        for row in reader:
            lines = row.split('\t')
            company = self.env.ref(str(lines[0]))
            country_id = self.env['res.country'].search([('name', '=', str(lines[1]))])

            self.env.cr.execute("UPDATE res_partner SET country_id = " + str(country_id.id) + " WHERE id = " + str(company.partner_id.id))
            company._compute_address()

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _raise_on_unreadable_pdfs(self, streams, stream_record):
        pass