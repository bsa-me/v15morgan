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

class BlomController(http.Controller):

    @http.route('/blomreceipt', type='http', auth="public", methods=['POST', 'GET'], csrf=False)
    def blom_return(self, **post):
        _logger.info('Beginning Blom Bank form_feedback with post data %s', pprint.pformat(post))
        order_ref = post['req_reference_number']
        _logger.info('Blom order ref is %s', order_ref)
        decision = post['decision']
        _logger.info('Decision is ' + decision)
        if decision == 'ACCEPT':
            _logger.info('Blom Bank Success')
            request.env['payment.transaction'].sudo().form_feedback(post, 'blom')

        return werkzeug.utils.redirect('/payment/process')