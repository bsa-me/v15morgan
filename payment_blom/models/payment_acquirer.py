# coding: utf-8

from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_blom.controllers.main import BlomController

import hashlib
import hmac
import uuid
import logging
from werkzeug import urls
import base64
import time
import random


_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    provider = fields.Selection(selection_add=[('blom', 'BLOM BANK')],ondelete={'blom': 'set none'})
    profile_id = fields.Char(string='Profile ID', required_if_provider='blom')
    access_key = fields.Char(string='Access Key', required_if_provider='blom')
    secret_key = fields.Char(string='Secret Key', required_if_provider='blom')

    def gmdate(self, str_formate, int_timestamp=None):
        if int_timestamp == None:
            return time.strftime(str_formate, time.gmtime())
        else:
            return time.strftime(str_formate, time.gmtime(int_timestamp))

    def _get_feature_support(self):
        res = super(PaymentAcquirer, self)._get_feature_support()
        res['fees'].append('blom')
        return res

    def sign(self,params):
        return self.signData(self.secret_key,self.buildDataToSign(params),'sha256')


    def signData(self,key, data, algo):
        dig = hmac.new( bytes(key,'ascii'), msg=bytes(data, 'ascii'), digestmod=algo)
        dig.digest()
        return base64.b64encode(dig.digest())

    def buildDataToSign(self,params):
        dataToSign = []
        signedFieldNames = params['signed_field_names'].split(",")
        for value in signedFieldNames:
            data = str(value) + "=" + str(params[value])
            dataToSign.append(data)

        return self.commaSeparate(dataToSign)

    def commaSeparate(self,dataToSign):
        return ','.join(dataToSign)


    @api.model
    def _get_blom_urls(self, environment):
        if environment == 'prod':
            return {
            'blom_form_url': 'https://secureacceptance.cybersource.com/pay',
            }

        else:
            return {
            'blom_form_url': 'https://testsecureacceptance.cybersource.com/pay',
            }

    def blom_form_generate_values(self, values):
        base_url = self.get_base_url()
        blom_tx_values = dict(values)
        blom_tx_values.update({
            'access_key': self.access_key,
            'profile_id': self.profile_id,
            'transaction_uuid': uuid.uuid1(),
            'signed_date_time': self.gmdate('%Y-%m-%dT%H:%M:%SZ'),
            'signed_field_names': 'bill_to_address_line2,amount,access_key,profile_id,transaction_uuid,signed_field_names,unsigned_field_names,signed_date_time,locale,transaction_type,reference_number,currency',
            'unsigned_field_names': 'bill_to_surname,bill_to_forename,bill_to_address_country,bill_to_address_line1,bill_to_address_city,bill_to_email,bill_to_phone',
            'locale': 'en',
            'currency': values['currency'] and values['currency'].name or '',
            'transaction_type': 'sale',
            'reference_number': random.randint(0, 10000000),
            'bill_to_forename': values.get('partner_first_name'),
            'bill_to_surname': values.get('partner_last_name'),
            'bill_to_phone': values.get('partner_phone'),
            'bill_to_email': values.get('partner_email'),
            'bill_to_address_line2': values.get('partner_address'),
            'bill_to_address_line1': values.get('partner_address'),
            'bill_to_address_city': values.get('partner_city'),
            'bill_to_address_country': values.get('partner_country') and values.get('partner_country').code or '',
            'amount': values['amount'],
            })
        signature = self.sign(blom_tx_values)
        blom_tx_values.update({
            'signature': signature,
            })

        order_ref = values['reference'].split('-')[0]
        order = self.env['sale.order'].sudo().search([('name','=',order_ref)])
        order.blom_order_ref = blom_tx_values['reference_number']

        return blom_tx_values

    def blom_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_blom_urls(environment)['blom_form_url']


class TxBlom(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _blom_form_get_tx_from_data(self, data):
        ref = data.get('req_reference_number')
        if not ref:
            error_msg = _('Blom: received data with missing reference')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        order = self.env['sale.order'].search([('blom_order_ref','=',ref)])
        tx = self.env['payment.transaction'].search([('reference', 'ilike', order.name)],limit=1)
        if not tx or len(tx) > 1:
            error_msg = _('Blom: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')

            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _blom_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if not data.get('signature'):
            invalid_parameters.append(('signature', data.get('signature'), 'something'))

        return invalid_parameters

    def _blom_form_validate(self, data):
        signature = data.get('signature', False)
        if signature:
            _logger.info('Blom signature ' + signature)
            self._set_transaction_done()
            return True

        else:
            error = _('Blom: feedback error')
            _logger.info(error)
            self.write({'state_message': error})
            self._set_transaction_cancel()
            return False
