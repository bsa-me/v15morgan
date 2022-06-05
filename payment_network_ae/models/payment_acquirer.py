# coding: utf-8

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


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    provider = fields.Selection(selection_add=[('networkae', 'Network AE')],ondelete={'networkae': 'set none'})
    api_url = fields.Char('API URL')
    network_api_key = fields.Char(string='API Key')
    outlet_url = fields.Char('Outlet URL')

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'networkae':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_network_ae.payment_method_networkae').id

    @api.model
    def _networkae_get_api_url(self, environment):
        return {'networkae_form_url': self.api_url}


    def get_access_token(self, content_type='application/vnd.ni-identity.v1+json'):
        payload = ""
        url = self.api_url + '/identity/auth/access-token'
        _logger.info('Access Token Url: ' + url)
        headers = {
        'Content-Type': content_type,
        'Authorization': 'Basic:' + self.network_api_key
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if 'access_token' in data:
            return 'Bearer ' + data['access_token']

        return False

    def create_api_order(self, access_token, url, payload, content_type='application/vnd.ni-payment.v2+json', accept='application/vnd.ni-payment.v2+json'):
        if access_token:
            headers = {
            'Content-Type': content_type,
            'Accept': accept,
            'Authorization': access_token
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            return response.json()

    def _networkae_make_request(self, values):
        base_url = self.get_base_url()
        networkae_tx_values = dict(values)
        date = datetime.now().strftime('%Y-%m-%d')
        access_token = self.get_access_token()
        url = self.api_url + '/transactions/outlets/' + self.outlet_url + '/orders'
        currency = self.env['res.currency'].search([('name','=',values['currency'].name)],limit=1)
        amount = values['amount'] * 100
        amount = currency._convert(amount,self.env.ref('base.AED'),self.company_id,date)

        amount = str(amount)
        if "." in amount:
            amount = amount.split(".")[0]

        payload = {
        "action": "SALE",
        "amount" : {"currencyCode" : "AED", "value" : amount},
        "emailAddress": values.get('partner_email'),
        "merchantAttributes": {"redirectUrl": urls.url_join(base_url, NetworkAEController._return_url)}
        }

        payload = json.dumps(payload)

        _logger.info('Create Order Url: ' + url)
        data = self.create_api_order(access_token, url, payload)
        _logger.info(data)

        order_url = data['_links']['payment']['href']

        values.update({
            'order_url': order_url
            })
        order_ref = values['reference'].split('-')[0]
        order = self.env['sale.order'].search([('name','=',order_ref),('company_id','=',self.company_id.id)])
        order.network_ae_order_ref = data['reference']

        return values

    def networkae_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_networkae_urls(environment)['networkae_form_url']
