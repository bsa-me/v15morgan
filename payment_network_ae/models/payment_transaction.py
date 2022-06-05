# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
import uuid
import logging
import requests
import json
from datetime import datetime
from odoo.addons.payment_network_ae.controllers.main import NetworkAEController
from werkzeug import urls
_logger = logging.getLogger(__name__)
from odoo.addons.payment.models.payment_acquirer import ValidationError



class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'networkae':
            return res
        base_url = self.get_base_url()
        networkae_tx_values = dict(processing_values)
        date = datetime.now().strftime('%Y-%m-%d')
        access_token = self.acquirer_id.get_access_token()
        url = self.acquirer_id.api_url + '/transactions/outlets/' + self.acquirer_id.outlet_url + '/orders'
        currency = self.env['res.currency'].browse(processing_values['currency_id'])
        amount = processing_values['amount'] * 100
        amount = currency._convert(amount,self.env.ref('base.AED'),self.acquirer_id.company_id,date)

        amount = str(amount)
        if "." in amount:
            amount = amount.split(".")[0]

        payload = {
        "action": "SALE",
        "amount" : {"currencyCode" : "AED", "value" : amount},
        "emailAddress": processing_values.get('partner_email'),
        "merchantAttributes": {"redirectUrl": urls.url_join(base_url, NetworkAEController._return_url)}
        }

        payload = json.dumps(payload)

        _logger.info('Create Order Url: ' + url)
        data = self.acquirer_id.create_api_order(access_token, url, payload)
        _logger.info(data)
        
        order_url = data['_links']['payment']['href']

        processing_values.update({
            'order_url': order_url
            })
        order_ref = processing_values['reference'].split('-')[0]
        order = self.env['sale.order'].search([('name','=',order_ref),('company_id','=',self.company_id.id)])
        order.network_ae_order_ref = data['reference']

        return processing_values
        

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'networkae':
            return tx

        _logger.info("Data Received: " + str(data))
        ref = data.get('reference')
        if not ref:
            error_msg = _('Network AE: received data with missing reference')
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        
        order = self.env['sale.order'].search([('network_ae_order_ref','=',ref)])
        tx = self.env['payment.transaction'].search([('reference', 'ilike', order.name)],limit=1)
        if not tx or len(tx) > 1:
            error_msg = _('Network AE: received data for reference %s') % (ref)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')

            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    @api.model
    def _networkae_form_get_tx_from_data(self, data):
        ref = data.get('reference')
        if not ref:
            error_msg = _('Network AE: received data with missing reference')
            _logger.info(error_msg)

        order = self.env['sale.order'].search([('network_ae_order_ref','=',ref)])
        tx = self.env['payment.transaction'].search([('reference', 'ilike', order.name)],limit=1)
        if not tx or len(tx) > 1:
            error_msg = _('Network AE: received data for reference %s') % (ref)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')

            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _networkae_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if not data.get('state'):
            invalid_parameters.append(('state', data.get('state'), 'something'))

        return invalid_parameters

    def _process_feedback_data(self, data):
        super()._process_feedback_data(data)
        if self.provider != 'networkae':
            return
        
        _logger.info('Return Status Is: ' + str(data))
        status = data.get('state', 'FAILED')
        if '_embedded' in data:
            if 'payment' in data['_embedded']:
                if data['_embedded']['payment']:
                    status = data['_embedded']['payment'][0]['state']
        
        if status in ['AUTHORISED','CAPTURED']:
            self._set_done()
            return True

        elif status == 'AWAIT_3DS':
            self._set_transaction_pending()
            return True

        else:
            error = _('NetworkAE: feedback error')
            _logger.info(error)
            self.write({'state_message': error})
            self._set_canceled()
            return False

    def _networkae_form_validate(self, data):
        status = data.get('state', 'FAILED')
        if status in ['AUTHORISED','CAPTURED']:
            self._set_done()
            return True
            

        elif status == 'AWAIT_3DS':
            self._set_pending()
            return True

        else:
            error = _('NetworkAE: feedback error')
            _logger.info(error)
            self._set_error("NetworkAE: " + error)
            self._set_canceled()
            return False