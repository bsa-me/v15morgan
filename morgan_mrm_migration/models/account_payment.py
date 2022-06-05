from odoo import models, fields
from odoo.exceptions import UserError


class Payment(models.Model):
	_inherit = 'account.payment'
	from_mrm = fields.Boolean('MRM')
	amount_receipt = fields.Monetary(string='Real Amount',compute="_compute_amount")
	invoice_allocation = fields.Char('Allocation',compute="_compute_allocation")
	#parent_company_id = fields.Many2one('res.company',related="company_id.parent_id",string="Company",store=True)
	
	def _compute_amount(self):
		for record in self:
			record['amount_receipt'] = record.amount
			if record.payment_type == 'outbound':
				record['amount_receipt'] = -record.amount
	
	def _compute_allocation(self):
		for record in self:
			record['invoice_allocation'] = ''
			if record.invoice_ids:
				invoices = record.invoice_ids.mapped('name')
				record['invoice_allocation'] = ','.join([str(inv) for inv in invoices])
