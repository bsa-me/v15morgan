
from odoo import api, models,fields,_
from odoo.exceptions import UserError,ValidationError
from datetime import datetime


class AccountPayment(models.Model):
	_inherit = "account.payment"
	show_payment_matching = fields.Boolean()
	allocated = fields.Boolean()
	payment_mode = fields.Selection([('cash', 'Cash'),('cheque', 'Cheque'),('credit_card', 'Credit Card'), ('transfer', 'Transfer')],string='Payment Mode',required=False)
	date_cleared = fields.Date('Date Cleared')
	payment_ref = fields.Char('Payment Reference', required=False)
	comment = fields.Text('Comments')
	reconciled_invoice_ids = fields.Many2many('account.move', string='Reconciled Invoices', compute=False, store=True, help="Invoices whose journal items have been reconciled with these payments.")
	company_id = fields.Many2one(string="Region", domain="[('is_region', '=', True)]",default=lambda self: self._get_child_companies(),store=True,readonly=False,related=False)
	journal_id = fields.Many2one(string='Bank Account')
	partial_reconcile_ids = fields.Many2many('account.partial.reconcile',string='Partial Reconcile')
	local_payment_amount = fields.Float(string='Local Payment Amount',compute="compute_local")
	#local_currency_id = fields.Many2one('res.currency',related='company_id.currency_id')
	


	def compute_local(self):
		for record in self:
			date = record.payment_date
			if record.from_mrm:
				date = datetime.now().strftime('%Y-%m-%d')
			record['local_payment_amount'] = record.currency_id._convert(record.amount,record.company_id.currency_id,record.company_id,date)

	@api.onchange('journal_id')
	def onchange_journal(self):
		if self.journal_id:
			self.currency_id = self.journal_id.company_id.currency_id.id


	def _prepare_payment_moves(self):
		all_move_vals = []
		for payment in self:
			company_currency = payment.company_id.currency_id
			move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

			write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
			if payment.payment_type in ('outbound', 'transfer'):
				counterpart_amount = payment.amount
				liquidity_line_account = payment.journal_id.default_debit_account_id
			else:
				counterpart_amount = -payment.amount
				liquidity_line_account = payment.journal_id.default_credit_account_id

			if payment.currency_id == company_currency:
				balance = counterpart_amount
				write_off_balance = write_off_amount
				counterpart_amount = write_off_amount = 0.0
				currency_id = False

			else:
				balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
				write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
				currency_id = payment.currency_id.id

			if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
				if payment.journal_id.currency_id == company_currency:

					liquidity_line_currency_id = False

				else:
					liquidity_line_currency_id = payment.journal_id.currency_id.id

				liquidity_amount = company_currency._convert(
					balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)

			else:
				liquidity_line_currency_id = currency_id
				liquidity_amount = counterpart_amount

			rec_pay_line_name = ''
			if payment.payment_type == 'transfer':
				rec_pay_line_name = payment.name

			else:
				if payment.partner_type == 'customer':
					if payment.payment_type == 'inbound':
						rec_pay_line_name += _("Customer Payment")
					elif payment.payment_type == 'outbound':
						rec_pay_line_name += _("Customer Credit Note")

				elif payment.partner_type == 'supplier':
					if payment.payment_type == 'inbound':
						rec_pay_line_name += _("Vendor Credit Note")
					elif payment.payment_type == 'outbound':
						rec_pay_line_name += _("Vendor Payment")


				if payment.invoice_ids:
					rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

			if payment.payment_type == 'transfer':
				liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
			else:
				liquidity_line_name = payment.name

			move_vals = {
			'date': payment.payment_date,
			'ref': payment.communication,
			'journal_id': payment.journal_id.id,
			'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
			'partner_id': payment.partner_id.id,
			'company_id': payment.company_id.id,
			'line_ids': [
			(0, 0, {
				'name': rec_pay_line_name,
				'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
				'currency_id': currency_id,
				'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
				'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
				'date_maturity': payment.payment_date,
				'partner_id': payment.partner_id.commercial_partner_id.id,
				'account_id': payment.destination_account_id.id,
				'payment_id': payment.id,
				'company_id': payment.company_id.id,
                    }),
			(0, 0, {
				'name': liquidity_line_name,
				'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
				'currency_id': liquidity_line_currency_id,
				'debit': balance < 0.0 and -balance or 0.0,
				'credit': balance > 0.0 and balance or 0.0,
				'date_maturity': payment.payment_date,
				'partner_id': payment.partner_id.commercial_partner_id.id,
				'account_id': liquidity_line_account.id,
				'payment_id': payment.id,
				}),
			],
			}

			if write_off_balance:
				move_vals['line_ids'].append((0, 0, {
					'name': payment.writeoff_label,
					'amount_currency': -write_off_amount,
					'currency_id': currency_id,
					'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
					'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
					'date_maturity': payment.payment_date,
					'partner_id': payment.partner_id.commercial_partner_id.id,
					'account_id': payment.writeoff_account_id.id,
					'payment_id': payment.id,
					}))

			if move_names:
				move_vals['name'] = move_names[0]

			all_move_vals.append(move_vals)

			if payment.payment_type == 'transfer':
				journal = payment.destination_journal_id

				if journal.currency_id and payment.currency_id != journal.currency_id:
					liquidity_line_currency_id = journal.currency_id.id
					transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id, payment.payment_date)

				else:
					liquidity_line_currency_id = currency_id
					transfer_amount = counterpart_amount

				transfer_move_vals = {
				'date': payment.payment_date,
				'ref': payment.communication,
				'partner_id': payment.partner_id.id,
				'journal_id': payment.destination_journal_id.id,
				'line_ids': [
				(0, 0, {
					'name': payment.name,
					'amount_currency': -counterpart_amount if currency_id else 0.0,
					'currency_id': currency_id,
					'debit': balance < 0.0 and -balance or 0.0,
					'credit': balance > 0.0 and balance or 0.0,
					'date_maturity': payment.payment_date,
					'partner_id': payment.partner_id.commercial_partner_id.id,
					'account_id': payment.company_id.transfer_account_id.id,
					'payment_id': payment.id,
					}),
				(0, 0, {
					'name': _('Transfer from %s') % payment.journal_id.name,
					'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
					'currency_id': liquidity_line_currency_id,
					'debit': balance > 0.0 and balance or 0.0,
					'credit': balance < 0.0 and -balance or 0.0,
					'date_maturity': payment.payment_date,
					'partner_id': payment.partner_id.commercial_partner_id.id,
					'account_id': payment.destination_journal_id.default_credit_account_id.id,
					'payment_id': payment.id,
					}),
				],
				}

				if move_names and len(move_names) == 2:
					transfer_move_vals['name'] = move_names[1]

				all_move_vals.append(transfer_move_vals)
		return all_move_vals

	def _get_child_companies(self):
		company = self.env.company
		child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
		if child_company:
			return child_company.id
		else:
			return company.id

	def open_register_payment_popup_form(self):

		ctx = {}

		ctx['default_payment_id'] = self.id
		ctx['default_partner_id'] = self.partner_id.id

		if self.payment_type == 'inbound':
			name = 'Register Payment'
			ctx['form_view_ref'] = 'invoice_custom_reconciliation.view_register_payment_form'

		else:
			name = 'Process Refund'
			ctx['form_view_ref'] = 'invoice_custom_reconciliation.view_register_refund_form'


		res = {
		'type': 'ir.actions.act_window',
		'name': name,
		'view_mode': 'form',
		'res_model': 'register.payment',
		'target': 'new',
		'context': ctx,
		}

		return res

	def post(self):

		res = super(AccountPayment, self).post()

		if self.show_payment_matching:
			return self.open_register_payment_popup_form()

		return res

	def action_draft(self):
		self.env['account.partial.reconcile'].search([('payment_id','=',self.id)]).unlink()
		return super(AccountPayment, self).action_draft()


