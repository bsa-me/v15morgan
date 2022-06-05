from odoo import http
from odoo.addons.sign.controllers.main import Sign

import base64
import io
import logging
import re

from PyPDF2 import PdfFileReader
from odoo.exceptions import UserError
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition

_logger = logging.getLogger()


class CustomSign(Sign):

    def get_document_qweb_context(self, id, token):
        sign_request = http.request.env['sign.request'].sudo().browse(id).exists()
        if not sign_request:
            if token:
                return http.request.render('sign.deleted_sign_request')
            else:
                return http.request.not_found()

        current_request_item = None
        if token:
            current_request_item = sign_request.request_item_ids.filtered(lambda r: r.access_token == token)
            if not current_request_item and sign_request.access_token != token and http.request.env.user.id != sign_request.create_uid.id:
                return http.request.render('sign.deleted_sign_request')
        elif sign_request.create_uid.id != http.request.env.user.id:
            return http.request.not_found()

        sign_item_types = http.request.env['sign.item.type'].sudo().search_read([])
        if current_request_item:
            for item_type in sign_item_types:
                if item_type['auto_field']:
                    fields = item_type['auto_field'].split('.')
                    if sign_request.template_id.fields_of == 'partner':
                        auto_field = current_request_item.partner_id
                    else:
                        auto_field = sign_request.template_id.event_reg_id
                    for field in fields:
                        if auto_field and field in auto_field:
                            auto_field = auto_field[field]
                        else:
                            auto_field = ""
                            break
                    item_type['auto_field'] = auto_field
            if current_request_item.state != 'completed':
                """ When signer attempts to sign the request again,
                its localisation should be reset.
                We prefer having no/approximative (from geoip) information
                than having wrong old information (from geoip/browser)
                on the signer localisation.
                """
                current_request_item.write({
                    'latitude': request.session['geoip'].get('latitude') if 'geoip' in request.session else 0,
                    'longitude': request.session['geoip'].get('longitude') if 'geoip' in request.session else 0,
                })

        item_values = {}
        sr_values = http.request.env['sign.request.item.value'].sudo().search(
            [('sign_request_id', '=', sign_request.id), '|', ('sign_request_item_id', '=', current_request_item.id),
             ('sign_request_item_id.state', '=', 'completed')])
        for value in sr_values:
            item_values[value.sign_item_id.id] = value.value

        Log = request.env['sign.log'].sudo()
        vals = Log._prepare_vals_from_item(
            current_request_item) if current_request_item else Log._prepare_vals_from_request(sign_request)
        vals['action'] = 'open'
        vals = Log._update_vals_with_http_request(vals)
        Log.create(vals)

        return {
            'sign_request': sign_request,
            'current_request_item': current_request_item,
            'token': token,
            'nbComments': len(sign_request.message_ids.filtered(lambda m: m.message_type == 'comment')),
            'isPDF': (sign_request.template_id.attachment_id.mimetype.find('pdf') > -1),
            'webimage': re.match('image.*(gif|jpe|jpg|png)', sign_request.template_id.attachment_id.mimetype),
            'hasItems': len(sign_request.template_id.sign_item_ids) > 0,
            'sign_items': sign_request.template_id.sign_item_ids,
            'item_values': item_values,
            'role': current_request_item.role_id.id if current_request_item else 0,
            'readonly': not (current_request_item and current_request_item.state == 'sent'),
            'sign_item_types': sign_item_types,
            'sign_item_select_options': sign_request.template_id.sign_item_ids.mapped('option_ids'),
        }
