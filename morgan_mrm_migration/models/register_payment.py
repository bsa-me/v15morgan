from odoo import models, fields
from odoo.exceptions import UserError


class RegiterPayment(models.Model):
    _inherit = 'register.payment'
    from_mrm = fields.Boolean('MRM')
    is_processed = fields.Boolean()


    def validate_payments(self):
        payments = self.search([('from_mrm','=',True),('payment_id.amount','>',0),('is_processed','=',False)],limit=500)
        for payment in payments:
        	try:
        		payment.action_register_payment()
        		payment.is_processed = True

        	except:
        		continue



