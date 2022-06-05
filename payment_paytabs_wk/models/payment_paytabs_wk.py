##########################################################################

import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api, _
from odoo.addons.payment_paytabs_wk.controllers.main import WebsiteSale
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.http import request
import requests
from ast import literal_eval
import json


class AcquirerPayTabs(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('paytabs', 'PayTabs')],ondelete={'paytabs': 'set none'})
    paytabs_client_id = fields.Char('Client Id' ,help = 'PayTabs Client Profile Id' ,required_if_provider='paytabs', groups='base.group_user')
    paytabs_client_secret = fields.Char('Secret API Key',help = 'PayTabs Client Secret API Key', required_if_provider='paytabs', groups='base.group_user')
    paytabs_domain = fields.Char('Client Domain',help = "Client Domain Based On Signup Region", required_if_provider='paytabs', groups='base.group_user')


    # @api.model
    # def get_paytabs_params(self, values):
    #     _logger.info('------------values-------------%r',values)

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'paytabs':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_paytabs_wk.payment_method_paytabs').id

# methoda called by form of paytabs for pass the form value
    def paytabs_form_generate_values(self, values):
        paytabs_tx_values = dict(values)
        paytabs_tx_values.update({
            'amount': values['amount'],
            'reference':str(values['reference']),
            'currency_code': values['currency'] and values['currency'].name or '',
        })
        return paytabs_tx_values

# methods of form action redirection of paytabs
    # def paytabs_get_form_action_url(self):
    #     self.ensure_one()
    #     return WebsiteSale._paytabs_feedbackUrl

    def detail_payment_acquire(self):
        return{
        "paytabs_client_secret":self.paytabs_client_secret,
        "paytabs_client_id":self.paytabs_client_id,
        "paytabs_domain":self.paytabs_domain,
        }



# transaction url for paytabs
    def paytabs_url(self):
        base_url = request.httprequest.host_url
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return{
        "pay_page_url"      : self.paytabs_domain + "/payment/request",
        "verify_payment"    : self.paytabs_domain + '/payment/query',
        'base_url' : base_url,
        'return_url': base_url+'paytabs/feedback',
        }


    def create_paytabs_params(self,partner,post):
        # def create_paytabs_params(self,partner,post):
        sale_order_detail = None
        products = ""
        qty = ""
        price_unit = ""
        order_line = []
        billing_address = ""
        address_shipping = ""

        if  "SO" in  post.get("reference")  :
            sale_order_detail = self.env['sale.order'].sudo().search([('name','=',post.get("reference").split('-')[0])])
            order_line = [sale_order_detail.order_line,True]
            billing_address =  sale_order_detail.partner_invoice_id
            address_shipping = sale_order_detail.partner_shipping_id

        elif  "INV"  in post.get("reference"):
            invoice_obj = self.env['account.move'].sudo().search([('name','=',post.get("reference").split('-')[0])])
            sale_order_detail = invoice_obj
            order_line = [invoice_obj.invoice_line_ids,False]
            billing_address = partner
            address_shipping = sale_order_detail.partner_shipping_id

        if not sale_order_detail:
            sale_order_detail = partner.last_website_so_id

        for i in order_line[0]:
            products = products +  i.product_id.name +" || "
            price_unit = price_unit +   str(i.price_unit) +" || "
            if order_line[1]:
                qty = qty + str(int(i.product_uom_qty)) +" || "

            else:
                qty = qty + str(int(i.quantity)) +" || "

        return products[0:len(products)-4],qty[0:len(qty)-4],price_unit[0:len(price_unit)-4],sale_order_detail,billing_address,address_shipping



class TransactionPayTabs(models.Model):
    _inherit = 'payment.transaction'


    paytabs_txn_id = fields.Char('Transaction ID')

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'paytabs':
            return res

        merchant_detail = self.acquirer_id
        order_ref = processing_values['reference'].split('-')[0]
        order = self.env['sale.order'].search([('name','=',order_ref),('company_id','=',self.company_id.id)])
        partner = order.partner_id
        total_amount = order.amount_total
        try:
            client_id = int(merchant_detail.paytabs_client_id)
        except Exception as e:
            _logger.warning("-------- Client Id issue ------ %r",e)
            return {"message":"Invalid client id "}
        paytabs_tx_values = {
                "profile_id": client_id,
                "payment_methods": ["all"],
                "tran_type": "sale",
                "tran_class": "ecom",
                "cart_id": order.name,
                "cart_currency": order.currency_id.name,
                "cart_amount": total_amount,
                "cart_description": order.name,
                "paypage_lang": "en",
                "customer_details": {
                    "name": str(partner.name),
                    "email": str(partner.email) or str(order.partner_id.email),
                    "phone": str(partner.phone),
                    "street1": str(partner.street),
                    "state": str(partner.state_id.name) or str(order.partner_shipping_id.name),
                    "city": str(partner.city) or str(order.partner_shipping_id.name),
                    "country": str(partner.country_id.code2)  or  str(order.partner_id.country_id.code2),
                    "zip": str(partner.zip),
                },
                "shipping_details": {
                    "name": str(partner.name),
                    "email": str(partner.email) or str(order.partner_id.email),
                    "phone": str(partner.phone),
                    "street1": str(partner.street),
                    "state": str(partner.state_id.name) or str(order.partner_shipping_id.name),
                    "city": str(partner.city) or str(order.partner_shipping_id.name),
                    "country": str(partner.country_id.code2)  or  str(order.partner_id.country_id.code2),
                    "zip":str(partner.zip),
                },
                "return": merchant_detail.paytabs_url().get('return_url'),
            }
        headers = {"authorization":merchant_detail.paytabs_client_secret,'Content-Type': 'application/json'}
        result = requests.post(url= merchant_detail.paytabs_url().get('pay_page_url'),headers = headers, data=json.dumps(paytabs_tx_values))
        request_params = literal_eval(result.text)
        if request_params.get("tran_ref"):
            self.acquirer_reference = request_params.get("tran_ref")
        
        return request_params


    @api.model
    def _paytabs_form_get_tx_from_data(self,  data):
        reference = data.get('cart_id')
        tx = self.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('PayTabs: received data with missing reference (%s)') % (reference)
            if not tx.ids:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            raise ValidationError(error_msg)
        return tx

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'paytabs':
            return tx
        reference = data.get('cart_id')
        tx = self.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('PayTabs: received data with missing reference (%s)') % (reference)
            if not tx.ids:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            raise ValidationError(error_msg)
        return tx

    def _paytabs_form_validate(self, data):
        res = {}
        payment_data = data.get('payment_result')
        tx = data.get("paytabs_transaction_id")
        if payment_data.get("response_message") == 'Authorised' and payment_data.get("response_status") == "A":
            res = {
            'acquirer_reference': tx,
            'paytabs_txn_id': tx,
            }
            self.write(res)
            return self._set_transaction_done()
        else:
            if payment_data.get("response_message") == "Cancelled":
                res.update({
                'paytabs_txn_id': tx,
                })
                self.write(res)
                return self._set_transaction_cancel()
            else:
                res.update({
                    'paytabs_txn_id': tx,
                    'acquirer_reference': tx,
                    })
                self.write(res)
                return self._set_transaction_pending()

    def _process_feedback_data(self, data):
        super()._process_feedback_data(data)
        if self.provider != 'paytabs':
            return
        
        res = {}
        payment_data = data.get('payment_result')
        tx = data.get("paytabs_transaction_id")
        if payment_data.get("response_message") == 'Authorised' and payment_data.get("response_status") == "A":
            res = {
            'date':fields.datetime.now(),
            }
            #self.write(res)
            return self._set_done()
        else:
            if payment_data.get("response_message") in ["Cancelled","Invalid card number"]:
                res.update({
                #'date':fields.datetime.now(),
                'paytabs_txn_id': tx,
                })
                self.write(res)
                return self._set_cancel()
            else:
                res.update({
                    'paytabs_txn_id': tx,
                    'acquirer_reference': tx,
                    #'date':fields.datetime.now(),
                    })
                self.write(res)
                return self._set_pending()
