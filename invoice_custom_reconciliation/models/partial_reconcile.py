
from odoo import api, models,fields,_
from odoo.exceptions import UserError


class PartialReconcile(models.Model):
	_inherit = "account.partial.reconcile"
	is_refund = fields.Boolean()
	payment_id = fields.Many2one('account.payment','Payment')


