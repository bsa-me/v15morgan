
from odoo import api, models, fields
from odoo.exceptions import UserError


class Payment(models.Model):
	_inherit = "account.payment"
	from_mrm = fields.Boolean('MRM')
	amount_receipt = fields.Monetary(string='Real Amount',compute="_compute_amount")
	invoice_allocation = fields.Char('Allocation',compute="_compute_allocation")
	parent_company_id = fields.Many2one('res.company',related="company_id.parent_id",string="Company",store=True)
	
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


	def action_post(self):
		code = 'account.payment'
		ref = 'RC-'
		name = False
		

		if self.payment_type=='outbound':
			code = 'account.payment.refund'
			ref = 'RF-'

		
		company_sequence = False
		parent_sequence = False
		
		if ref not in self.name:
			if(not self.company_id.document_sequence):
				company_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.id),('code','=',code)],limit=1)
				name = ref + self.company_id.code+'-'+str(company_sequence.next_by_id())

			else:
				parent_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.parent_id.id),('code','=',code)],limit=1)
				if(parent_sequence):
					name = ref+self.company_id.parent_id.code+'-'+str(parent_sequence.next_by_id())

			self.write({'name': name})

		move_id = self.env['account.move.line'].search([('payment_id','=',self.id)],limit=1).move_id
		move_id.write({'name': self.name, 'company_id': self.company_id.id})

		return super(Payment, self).action_post()

	@api.onchange('amount', 'currency_id')
	def _onchange_amount(self):
		journal = self.env['account.journal'].search([('company_id','=',self.company_id.id),('type','=','bank')],limit=1)
		if journal:
			self.journal_id = journal.id
			
	"""@api.onchange('payment_type')
	def _onchange_payment_type(self):
		if not self.invoice_ids and not self.partner_type:
			if self.payment_type == 'inbound':
				self.partner_type = 'customer'

			elif self.payment_type == 'outbound':
				self.partner_type = 'supplier'

		elif self.payment_type not in ('inbound', 'outbound'):
			self.partner_type = False

		res = self._onchange_journal()
		if not res.get('domain', {}):
			res['domain'] = {}

		jrnl_filters = self._compute_journal_domain_and_types()
		journal_types = jrnl_filters['journal_types']
		journal_types.update(['bank'])
		return res"""

		