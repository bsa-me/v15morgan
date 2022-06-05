
from odoo import api, models,fields
from odoo.exceptions import UserError,ValidationError


class RegisterPaymentLine(models.Model):
	_name = "register.payment.line"

	move_id = fields.Many2one('account.move',string='Invoice')
	amount = fields.Float(string='Amount')
	allocated_amount = fields.Float('Allocated Amount')
	currency_id = fields.Many2one('res.currency',related='move_id.currency_id')
	payment_currency = fields.Many2one('res.currency',related="payment_registration_id.payment_id.currency_id")
	payment_registration_id = fields.Many2one('register.payment')
	partner_id = fields.Many2one('res.partner')
	payment_id = fields.Many2one('account.payment',related="payment_registration_id.payment_id")


	@api.onchange('move_id')
	def onchange_amount(self):
		over_due = self.move_id.over_due_payment
		if over_due < 0:
			self.amount = -over_due

	"""@api.constrains('amount')
	def check_amount(self):
		due_amount = self.move_id.amount_residual
		if self.move_id.amount_residual < 0:
			due_amount = - self.move_id.amount_residual
		
		if self.amount > due_amount and due_amount > 0:
			raise ValidationError('the amount of the payment should not exceed the due amount of the invoice')"""


