
from odoo import api, models,fields,_
from odoo.exceptions import UserError


class AccountMove(models.Model):
	_inherit = "account.move"
	company_id = fields.Many2one('res.company',string='Region', store=True, readonly=True, related=False, change_default=True)
	amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_amount_undiscounted', digits=0)
	amount_discount = fields.Float(string='Total Discount',compute="get_amount_discount")
	mrm_id = fields.Integer('MRM ID')
	mrm_lifecycle_status = fields.Char('MRM status')
	mrm_pdf = fields.Many2one('ir.attachment',string='MRM PDF')
	study_format = fields.Char('Study Format')
	terms = fields.Char('Terms')
	categories = fields.Char('Categories')
	items_and_events = fields.Char('Items/Events')
	total_open_fps = fields.Integer('Total Open Fps')
	other_inv_ref = fields.Char()
	note = fields.Text()
	amount_untaxed_sign = fields.Monetary(compute="_compute_amount_sign")
	amount_tax_sign = fields.Monetary(compute="_compute_amount_sign")
	amount_total_sign = fields.Monetary(compute="_compute_amount_sign")

	def _compute_amount_undiscounted(self):
		for move in self:
			total = 0.0
			for line in move.invoice_line_ids:
				total += line.price_subtotal + line.price_unit * ((line.discount or 0.0) / 100.0) * line.quantity

			move.amount_undiscounted = total

	def get_amount_discount(self):
		for record in self:
			record.amount_discount = 0
			discount = 0
			reward_lines = record.invoice_line_ids.filtered(lambda l: l.price_unit < 0)
			discount += -sum(reward_lines.mapped('price_subtotal'))
			discount_lines = record.invoice_line_ids.filtered(lambda l: l.discount > 0)
			for line in discount_lines:
				discount += line.price_unit * line.quantity - line.price_subtotal

			record.amount_discount = discount

	@api.model
	def _get_default_journal(self):
		move_type = self._context.get('default_type', 'entry')
		journal_type = 'general'
		if move_type in self.get_sale_types(include_receipts=True):
			journal_type = 'sale'

		elif move_type in self.get_purchase_types(include_receipts=True):
			journal_type = 'purchase'

		if self._context.get('default_journal_id'):
			journal = self.env['account.journal'].browse(self._context['default_journal_id'])

			if move_type != 'entry' and journal.type != journal_type:
				raise UserError(_("Cannot create an invoice of type %s with a journal having %s as type.") % (move_type, journal.type))

		else:
			company = False
			if self.company_id:
				company = self.company_id
			else:
				company = self.env.company
			company_id = self._context.get('force_company', self._context.get('default_company_id', company.id))
			domain = [('company_id', '=', company_id), ('type', '=', journal_type)]

			journal = None
			if self._context.get('default_currency_id'):
				currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
				journal = self.env['account.journal'].search(currency_domain, limit=1)

			if not journal:
				journal = self.env['account.journal'].search(domain, limit=1)


			if not journal:
				error_msg = _('Please define an accounting miscellaneous journal in your company')
				if journal_type == 'sale':
					error_msg = _('Please define an accounting sale journal in your company')
				elif journal_type == 'purchase':
					error_msg = _('Please define an accounting purchase journal in your company')
				raise UserError(error_msg)
		return journal
	
	def action_cancel(self):
		res = super(AccountMove, self).action_cancel()
		if res and not self.env.context.get('is_merge', False):
			self.mapped('invoice_line_ids.sale_line_ids.registration_ids').filtered
			(lambda x: x.state not in ['done', 'draft']).action_set_draft()
			return res

	def unlink(self):
		registrations = self.env['event.registration'].sudo()
		registrations = registrations.search([('sale_order_line_id', 'in', self.invoice_line_ids.sale_line_ids.ids)])
		res = super(AccountMove, self).unlink()
		if registrations:
			registrations.filtered(
				lambda x: x.state not in ['done', 'draft']).action_set_draft()

	def action_invoice_draft(self):
		res = super(AccountMove, self).action_invoice_draft()
		if res:
			self._confirm_attendees()

	def action_post(self):
		#raise UserError('test')
		res = super(AccountMove, self).action_post()
		code = 'account.move'
		ref = False
		name = False
		reversed_entry = False
		if(self.move_type=='out_invoice'):
			ref = 'SI'

		elif(self.move_type=='out_refund'):
			ref = 'CR'
			reversed_entry = self.reversed_entry_id

		company_sequence = False
		parent_sequence = False

		if ref and ref not in self.name:
			if(not self.company_id.document_sequence):
				company_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.id),('code','=',code),('prefix','=','SI')],limit=1)
				name = ref + self.company_id.code+'-'+str(company_sequence.number)
				company_sequence.write({'number': company_sequence.number + 1})

			else:
				parent_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.parent_id.id),('code','=',code),('prefix','=','SI')],limit=1)
				if(parent_sequence):
					name = ref+self.company_id.parent_id.code+'-'+str(parent_sequence.number)
					parent_sequence.write({'number': parent_sequence.number + 1})

			self.write({'name': name})
			

		if self.invoice_origin:
			order = self.env['sale.order'].search([('name','=',self.invoice_origin)],order='id desc',limit=1)
			for line in order.order_line:
				if line.event_id:
					self.env['event.registration'].search([('event_id','=',line.event_id.id),('sale_order_id','=',order.id)]).action_confirm()

				if line.session_id:
					self.env['event.registration'].search([('session_id','=',line.session_id.id),('sale_order_id','=',order.id)]).action_confirm()

		if self.invoice_picking_id:
			self.invoice_picking_id.write({'origin': self.name})
		
		if reversed_entry:
			reversed_entry.js_assign_outstanding_line(
				self.line_ids.filtered(lambda l: l.account_id.user_type_id.name == 'Receivable').id)
			

		return res
	def _compute_amount_sign(self):
		for record in self:
			record['amount_untaxed_sign'] = record.amount_untaxed
			record['amount_tax_sign'] = record.amount_tax
			record['amount_total_sign'] = record.amount_total
			
			if record.move_type == 'out_refund':
				record['amount_untaxed_sign'] = -record.amount_untaxed
				record['amount_tax_sign'] = -record.amount_tax
				record['amount_total_sign'] = -record.amount_total
		