# -*- coding: utf-8 -*-

import json
import logging
import pprint

import requests
import werkzeug

from odoo import http
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

class NetworkAEController(http.Controller):
    _return_url = '/ngenius_callback'

    @http.route(['/ngenius_callback'], type='http', auth='public', csrf=False)
    def networkae_return(self, **post):
        order_ref = post['ref']
        order = request.env['sale.order'].search([('network_ae_order_ref','=',order_ref)])

        _logger.info('Nework AE order ref is %s', order_ref)
        website_id = order.website_id.id
        payment_acquirer_id = 23
        if website_id == 8:
            payment_acquirer_id = 22
        elif website_id == 11:
            payment_acquirer_id = 24
        elif website_id == 7:
            payment_acquirer_id = 16
        elif website_id == 12:
            payment_acquirer_id = 25
        elif website_id == 13:
            payment_acquirer_id = 26
        elif website_id == 1:
            payment_acquirer_id = 27
        elif website_id == 20:
            payment_acquirer_id = 37
        payment_acquirer = request.env['payment.acquirer'].browse(payment_acquirer_id)
        order_status_url = payment_acquirer.api_url + '/transactions/outlets/' + payment_acquirer.outlet_url + '/orders/' + order_ref
        _logger.info('Return Order Url: ' + order_status_url)
        access_token = payment_acquirer.get_access_token()
        headers = {
        'Authorization': access_token,
        }
        response = requests.request("GET", order_status_url, headers=headers, data={})
        data = response.json()
        order_status = ''
        if '_embedded' in data and data['_embedded']:
            if 'payment' in data['_embedded'] and data['_embedded']['payment']:
                order_status = data['_embedded']['payment'][0]['state']
        _logger.info('Order Status ' + order_status)
        post.update({'state': order_status})
        if post.get('state') in ['AUTHORISED','CAPTURED']:
            request.env['payment.transaction'].sudo()._handle_feedback_data('networkae', data)

        return werkzeug.utils.redirect('/payment/status')


