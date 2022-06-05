from odoo.exceptions import ValidationError,UserError
from odoo import models, fields, api, _
from datetime import datetime


class FuturePayment(models.Model):
	_name = 'morgan.future.payment'
	name = fields.Char(string='Name')
	partner_id = fields.Many2one('res.partner',string='Account')
	amount = fields.Float(string='Amount')
	currency_id = fields.Many2one('res.currency',string='Currency',related='invoice_id.currency_id')
	due_amount = fields.Float(string='Due Amount')
	due_date = fields.Date(string='Due Date')
	invoice_id = fields.Many2one('account.move',string='Invoice')
	status = fields.Selection([('open','Open'),('partially','Partially Paid'),('paid','Paid'),('fullyrefunded','Fully Refunded'),('partialrefunded','Partially Refunded')],string='Status',compute="_compute_status",store=True)
	region_id = fields.Many2one('res.company',string='Region')
	company_id = fields.Many2one(related='region_id.parent_id',string='Company')
	is_covered = fields.Boolean()
	amount_usd = fields.Float('Amount($)')
	currency_usd = fields.Many2one('res.currency',compute="_compute_currency_usd")
	product_categories = fields.Char('Product Categories',store=False,related="invoice_id.categories")
	terms = fields.Char('Terms',store=False,compute="_compute_info")
	total_invoiced_amount = fields.Monetary(currency_field='currency_id',store=True,string='Total Invoiced'
		,compute="_compute_total_invoiced")


	def _compute_currency_usd(self):
		for record in self:
			record['currency_usd'] = self.env.ref('base.USD').id


	@api.onchange('amount')
	def on_change_amount(self):
		self.due_amount = self.amount
		return {
			'value': {'due_amount': self.amount},
			  	
		}

	
	@api.model
	def create(self, vals):
		record = super(FuturePayment, self).create(vals)


		if not record.from_mrm:
			date = datetime.now().strftime('%Y-%m-%d')
			company_sequence = False
			parent_sequence = False
			amount = record.amount
			if 'amount' in vals:
				amount = vals['amount']

			due_date = record.due_date
			if 'due_date' in vals:
				due_date = vals['due_date']

			region = record.region_id
			if 'region_id' in vals:
				region = self.env['res.company'].browse(vals['region_id'])

			company = record.company_id
			if 'company_id' in vals:
				company = self.env['res.company'].browse(vals['company_id'])

			amount_usd = record.currency_id._convert(amount,self.env.ref('base.USD'),region,date)
			record['amount_usd'] = amount_usd

			invoice = record.invoice_id
			if 'invoice_id' in vals:
				invoice = self.env['account.move'].browse(vals['invoice_id'])

			name = ''
			code = 'account.move.line'
			ref = 'FP-'
			if not record.name:
				if(not region.document_sequence):
					company_sequence = record.env['ir.sequence'].search([('company_id','=',region.id),('code','=',code),('prefix','=','FP')],limit=1)
					#raise UserError(str(ref) + str(record.region_id.code)+'-'+str(company_sequence.number))
					name = ref + region.code+'-'+str(company_sequence.number)
					company_sequence.write({'number': company_sequence.number + 1})

				else:
					parent_sequence = record.env['ir.sequence'].search([('company_id','=',region.parent_id.id),('code','=',code),('prefix','=','FP')],limit=1)
					if(parent_sequence):
						name = ref+region.parent_id.code+'-'+str(parent_sequence.number)
						parent_sequence.write({'number': parent_sequence.number + 1})

				record['name'] = name

				move_line = self.env['account.move.line'].search([('name','=',name),('move_id','in',invoice.ids),('is_future_payment','=',True),('line_type','=','out_invoice')])
				if not move_line:
					account = self.env['account.move.line'].search([('move_id','in',invoice.ids),('account_id.user_type_id.name','in',['Receivable','Recevable'])],limit=1).account_id
					move_line = self.env['account.move.line'].create({
						'name': name,
						'debit': invoice.currency_id._convert(amount,invoice.company_id.currency_id,invoice.company_id,date),
						'move_id': invoice.id,
						'account_id': account.id,
						'date_maturity': due_date,
						'company_id': region.id,
						'exclude_from_invoice_tab': True,
						'is_future_payment': True,
						'line_type': 'out_invoice',
						'partner_id': invoice.commercial_partner_id.id,
						})

		return record
	
	
	def write(self, vals):

		date = datetime.now().strftime('%Y-%m-%d')
		company_sequence = False
		parent_sequence = False
		amount = self.amount
		if 'amount' in vals:
			amount = vals['amount']

		due_date = self.due_date
		if 'due_date' in vals:
			due_date = vals['due_date']

		name = self.name
		if 'name' in vals:
			name = vals['name']


		company = self.company_id
		if 'company_id' in vals:
			company = self.env['res.company'].browse(vals['company_id'])

		region = self.region_id
		if 'region_id' in vals:
			region = self.env['res.company'].browse(vals['region_id'])

		invoice = self.invoice_id
		if 'invoice_id' in vals:
			invoice = self.env['account.move'].browse(vals['invoice_id'])

		if not self.from_mrm:
			if company:
				amount_usd = self.currency_id._convert(amount,self.env.ref('base.USD'),company,date)

			else:
				amount_usd = self.currency_id._convert(amount,self.env.ref('base.USD'),region,date)
			vals['amount_usd'] = amount_usd

			move_line = self.env['account.move.line'].search([('name','=',name),('move_id','in',invoice.ids)])
			#raise UserError(move_line.name)
			if move_line:
				move_line.write({
					'name': name,
					'debit': move_line.move_id.currency_id._convert(amount,move_line.company_currency_id,move_line.company_id,date),
					'date_maturity': due_date,
					})

		return super(FuturePayment, self).write(vals)



	@api.depends('due_amount', 'amount')
	def _compute_status(self):
		for record in self:
			record['status'] = False
			if record.due_amount == record.amount:
				record['status'] = 'open'
			
			elif record.due_amount <= 0:
				record['status'] = 'paid'

			elif record.due_amount > 0 and record.due_amount < record.amount:
				record['status'] = 'partially'

	@api.depends('invoice_id.invoice_line_ids')
	def _compute_info(self):
		for record in self:
			terms = ''
			categories = ''
			term_names = record.invoice_id.invoice_line_ids.mapped('term_id').mapped('name')
			category_names = record.invoice_id.invoice_line_ids.mapped('product_id').mapped('categ_id').mapped('name')

			if term_names:
				terms = '/'.join([term for term in term_names])

			if category_names:
				categories = '/'.join([category for category in category_names])

			record['terms'] = terms

	@api.depends('invoice_id.amount_total','invoice_id.amount_residual')
	def _compute_total_invoiced(self):
		for record in self:
			record.total_invoiced_amount = record.invoice_id.amount_total - record.invoice_id.amount_residual


