
from odoo import api, models,fields
from odoo.exceptions import UserError,ValidationError
from datetime import datetime


class MorganPayment(models.Model):
	_name = "register.payment"

	payment_id = fields.Many2one('account.payment')
	partner_id = fields.Many2one('res.partner')
	payment_line_ids = fields.One2many('register.payment.line','payment_registration_id',string='Invoices')
	payment_amount = fields.Monetary(related='payment_id.amount',string='Payment Amount')
	currency_id = fields.Many2one('res.currency',related='payment_id.currency_id')
	local_payment_amount = fields.Float(related='payment_id.local_payment_amount')
	#local_currency_id = fields.Many2one('res.currency',related='payment_id.company_id.currency_id')
	move_ids = fields.Many2many('account.move')


	@api.onchange('partner_id')
	def _onchange_partner(self):
		date = datetime.now().strftime('%Y-%m-%d')
		if self.payment_id.payment_type == 'inbound':
			self.env['register.payment.line'].search([('payment_registration_id','in',self.ids)]).unlink()
			res = {}
			partner = self.partner_id
			invoices = []
			partner_invoices = self.env['account.move'].search([('partner_id','=',partner.id),('type','=','out_invoice'),('state','!=','draft'),('amount_residual','>',0),('company_id','=',self.payment_id.company_id.id)])
			for inv in partner_invoices:
				if(inv.amount_residual > 0):
					line = self.env['register.payment.line'].create({
						'move_id': inv.id,
						'allocated_amount': inv.currency_id._convert(inv.amount_residual,self.payment_id.currency_id,inv.company_id,date),
						'amount': inv.amount_residual,
						'payment_registration_id': self.id
						})

		elif self.payment_id.payment_type == 'outbound':
			self.env['register.payment.line'].search([('payment_registration_id','in',self.ids)]).unlink()
			res = {}
			partner = self.partner_id
			invoices = []
			partner_invoices = self.env['account.move'].search([('partner_id','=',partner.id),('type','=','out_invoice'),('state','!=','draft'),('amount_residual','<',0),('company_id','=',self.payment_id.company_id.id)])
			for inv in partner_invoices:
				line = self.env['register.payment.line'].create({
					'move_id': inv.id,
					'amount': -inv.amount_residual,
					'allocated_amount': -inv.currency_id._convert(inv.amount_residual,self.payment_id.currency_id,inv.company_id,date),
					'payment_registration_id': self.id
					})

	@api.onchange('payment_line_ids')
	def onchange_payment_line_ids(self):
		moves = []
		for line in self.payment_line_ids:
			if line.move_id.id:
				moves.append(line.move_id.id)

		if moves:
			self.move_ids = [(6, 0, moves)]

	
	@api.constrains('payment_line_ids')
	def check_total_amount(self):
		total_amount = 0
		currency = False
		for line in self.payment_line_ids:
			total_amount = total_amount + line.allocated_amount
			if not currency:
				currency = line.move_id.currency_id

		amount = self.payment_id.currency_id._convert(self.payment_id.amount,currency,self.payment_id.company_id,self.payment_id.payment_date)
		#raise UserError(str(total_amount) + ' ' + str(amount))
		if round(total_amount, 2) != round(self.payment_amount,2):
			raise ValidationError('The total of the amount paid should be equal to the total amount of the payment!')


	def action_register_payment(self):
		self.ensure_one()
		date = datetime.now().strftime('%Y-%m-%d')
		moves = []
		payment = self.payment_id
		partner = self.partner_id
		journal_item = self.env['account.move.line'].search([('payment_id','in',self.ids),('credit','>',0)])
		#raise UserError(journal_item)

		if self.payment_id.payment_type == 'inbound':
			if self.payment_line_ids:
				partials = []
				for line in self.payment_line_ids:
					if line.move_id:
						date = self.payment_id.payment_date
						if self.payment_id.from_mrm:
							date = datetime.now().strftime('%Y-%m-%d')
						move_lines = []
						new_move = self.env['account.move'].with_context(force_company=self.payment_id.company_id.id).create({
							'partner_id': partner.id,
							'date': payment.payment_date,
							'company_id': self.payment_id.company_id.id,
							'journal_id': payment.journal_id.id,
							'is_payment_move': True,
							})
						account_id = self.env['account.account'].search([('company_id','=', self.payment_id.company_id.id),('code','in',['121000','121']),('name','=','Account Receivable')],limit=1).id
						first_move_line_vals = {}
						first_move_line_vals['partner_id'] = partner.id
						first_move_line_vals['account_id'] = account_id
						first_move_line_vals['credit'] = self.payment_id.currency_id._convert(line.allocated_amount,line.move_id.company_id.currency_id,line.move_id.company_id,date)
						#first_move_line_vals['credit'] = line.allocated_amount
						first_move_line_vals['date'] = self.payment_id.payment_date
						first_move_line_vals['debit'] = 0
						first_move_line_vals['move_id'] = new_move.id
						first_move_line_vals['payment_id'] = False

						move_lines.append((0, 0, first_move_line_vals))

						second_move_line_vals = {}
						second_move_line_vals['partner_id'] = partner.id
						second_move_line_vals['account_id'] = self.env['account.move.line'].search([('move_id','=',line.move_id.id),('exclude_from_invoice_tab','=',False)],limit=1).account_id.id
						second_move_line_vals['credit'] = 0
						second_move_line_vals['debit'] = self.payment_id.currency_id._convert(line.allocated_amount,line.move_id.company_id.currency_id,line.move_id.company_id,date)
						#second_move_line_vals['debit'] = line.allocated_amount
						second_move_line_vals['payment_id'] = False
						second_move_line_vals['move_id'] = new_move.id
						second_move_line_vals['date'] = self.payment_id.payment_date

						move_lines.append((0, 0, second_move_line_vals))
						try:
							new_move['line_ids'] = move_lines
						except:
							print('test')
						new_move.post()

						amount = line.allocated_amount
						move_line_fps = self.env['account.move.line'].search([('move_id','=',line.move_id.id),('is_future_payment','=',1)],order='date_maturity asc')
						for move_line in move_line_fps:
							if amount > 0:
								due_amount = move_line.amount_residual
								if amount > due_amount:
									partial_reconcile = self.env['account.partial.reconcile'].create({
										'debit_move_id': move_line.id,
										'credit_move_id': self.env['account.move.line'].search([('move_id','=',new_move.id),('credit','>',0)],limit=1).id,
										'company_id': self.payment_id.company_id.id,
										'amount': self.payment_id.currency_id._convert(due_amount,move_line.company_currency_id,self.payment_id.company_id,date),
										'payment_id': self.payment_id.id,
										})
									

									partials.append(partial_reconcile.id)

								else:
									partial_reconcile = self.env['account.partial.reconcile'].create({
										'debit_move_id': move_line.id,
										'credit_move_id': self.env['account.move.line'].search([('move_id','=',new_move.id),('credit','>',0)],limit=1).id,
										'company_id': self.payment_id.company_id.id,
										'amount': self.payment_id.currency_id._convert(amount,move_line.company_currency_id,self.payment_id.company_id,date),
										'payment_id': self.payment_id.id,
										})

									partials.append(partial_reconcile.id)

								amount = amount - due_amount
								if amount <= 0:
									amount = 0
						

						mrm_future_payment = self.env['morgan.future.payment'].search([('invoice_id','=',line.move_id.id),('from_mrm','=',True),('due_amount','>',0)],order='due_date')
						amount = self.payment_id.currency_id._convert(line.allocated_amount,line.move_id.currency_id,self.payment_id.company_id,date)
						if amount > 0:
							for fp in mrm_future_payment:
								amount = fp.due_amount - amount
								if amount >= 0:
									fp.write({'due_amount': amount})
									break
								else:
									fp.write({'due_amount': 0})
									amount = -amount

						moves.append(line.move_id.id)
			if payment.invoice_ids:
				for inv in payment.invoice_ids:
					moves.append(inv.id)

			payment.write({'invoice_ids': [(6, 0, moves)], 'allocated': True, 'show_payment_matching': False, 'reconciled_invoice_ids': [(6, 0, moves)], 'state': 'reconciled', 'partial_reconcile_ids': [(6, 0, partials)]})
			self.env['account.move'].browse(moves).compute_over_due_payment()

		elif(self.payment_id.payment_type == 'outbound'):
			partials = []
			if self.payment_line_ids:
				for line in self.payment_line_ids:
					if line.move_id:
						date = self.payment_id.payment_date
						if self.payment_id.from_mrm:
							date = datetime.now().strftime('%Y-%m-%d')
						move_lines = []
						new_move = self.env['account.move'].with_context(force_company=self.payment_id.company_id.id).create({
							'partner_id': partner.id,
							'date': payment.payment_date,
							'company_id': self.payment_id.company_id.id,
							'journal_id': payment.journal_id.id,
							'is_payment_move': True,
							})

						account_id = self.env['account.account'].search([('company_id','=', self.payment_id.company_id.id),('code','=','121000'),('name','=','Account Receivable')],limit=1).id
						first_move_line_vals = {}
						first_move_line_vals['partner_id'] = partner.id
						first_move_line_vals['account_id'] = account_id
						first_move_line_vals['credit'] = 0
						first_move_line_vals['date'] = self.payment_id.payment_date
						first_move_line_vals['debit'] = self.payment_id.currency_id._convert(line.allocated_amount,line.move_id.company_id.currency_id,line.move_id.company_id,date)
						first_move_line_vals['move_id'] = new_move.id
						first_move_line_vals['payment_id'] = False

						move_lines.append((0, 0, first_move_line_vals))

						second_move_line_vals = {}
						second_move_line_vals['partner_id'] = partner.id
						second_move_line_vals['account_id'] = self.env['account.move.line'].search([('move_id','=',line.move_id.id),('exclude_from_invoice_tab','=',False)],limit=1).account_id.id
						second_move_line_vals['credit'] = self.payment_id.currency_id._convert(line.allocated_amount,line.move_id.company_id.currency_id,line.move_id.company_id,date)
						second_move_line_vals['debit'] = 0
						second_move_line_vals['payment_id'] = False
						second_move_line_vals['move_id'] = new_move.id
						second_move_line_vals['date'] = self.payment_id.payment_date

						move_lines.append((0, 0, second_move_line_vals))
						new_move['line_ids'] = move_lines
						new_move.post()
						
						account_move_line = self.env['account.move.line'].search([('move_id','=',line.move_id.id),('debit','>',0)],limit=1)
						if account_move_line:
							partial_reconcile = self.env['account.partial.reconcile'].create({
								'debit_move_id': self.env['account.move.line'].search([('move_id','=',line.move_id.id),('debit','>',0)],limit=1).id,
								'credit_move_id': self.env['account.move.line'].search([('move_id','=',new_move.id),('credit','>',0)],limit=1).id,
								'company_id': self.payment_id.company_id.id,
								'amount': -self.payment_id.currency_id._convert(line.allocated_amount,account_move_line.company_currency_id,account_move_line.move_id.company_id,date),
								'is_refund': 1,
								'payment_id': self.payment_id.id
								})
							partials.append(partial_reconcile.id)



						moves.append(line.move_id.id)
			if payment.invoice_ids:
				for inv in payment.invoice_ids:
					moves.append(inv.id)

			payment.write({'invoice_ids': [(6, 0, moves)], 'allocated': True, 'show_payment_matching': False, 'reconciled_invoice_ids': [(6, 0, moves)], 'state': 'reconciled', 'partial_reconcile_ids': [(6, 0, partials)]})
			self.env['account.move'].browse(moves).compute_over_due_payment()
			#payment.post()



