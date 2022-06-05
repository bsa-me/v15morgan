# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError

class account_move(models.Model):
	
	_inherit = 'account.move'
	_order = 'invoice_date_due'

	is_payment_move = fields.Boolean()
	total_signed_amount = fields.Float(compute="_get_total_signed")
	balance = fields.Float(compute="_compute_balance",store=False,string='Balance($)')
	is_statement = fields.Boolean(store=True,compute="_compute_is_statement")
	is_soa_statement = fields.Boolean(compute="_compute_is_soa")
	allocation_currency = fields.Many2one('res.currency',compute="_get_total_signed")
	amount_usd = fields.Float('Amount($)')
	dollar_amount = fields.Monetary(compute="_get_amount_usd",store=False,string='Amount($)')
	currency_usd = fields.Many2one('res.currency',compute="_compute_currency_usd")
	local_balance = fields.Float(compute="_compute_balance",store=False,string='Local Balance')
	soa_id = fields.Integer(related='id',store=False)
	soa_region = fields.Many2one(related='company_id',store=False)


	
	def _get_result(self):
		for aml in self:
			aml.result = 0.0
			aml.result = aml.amount_total_signed - aml.credit_amount 

	def _get_credit(self):
		for aml in self:
			aml.credit_amount = 0.0
			aml.credit_amount = aml.amount_total_signed - aml.amount_residual_signed

	credit_amount = fields.Float(compute ='_get_credit',   string="Credit/paid")
	result = fields.Float(compute ='_get_result',   string="Balance") #'balance' field is not the same

	
	def _get_total_signed(self):
		for record in self:
			date = fields.Date.context_today
			record['total_signed_amount'] = 0
			record['allocation_currency'] = record.currency_id.id
			if record.amount_total_signed:
				if record.name[:2] == 'RC':
					receipt = self.env['account.payment'].sudo().search([('name','=',record.name),('partner_id','=',record.partner_id.id)],limit=1)
					amount = record.amount_total if receipt.currency_id == record.currency_id else record.amount_total_signed
					if receipt.payment_date:
						date = receipt.payment_date

					if receipt.payment_type == 'inbound':
						record['total_signed_amount'] = -amount
					elif receipt.payment_type == 'outbound':
						record['total_signed_amount'] = amount
					record['allocation_currency'] = receipt.currency_id.id

				elif 'RF' in record.name:
					receipt = self.env['account.payment'].sudo().search([('name','=',record.name),('partner_id','=',record.partner_id.id)],limit=1)
					record['total_signed_amount'] = record.amount_total
					record['allocation_currency'] = receipt.currency_id.id

					


				elif 'CR' in record.name and 'SI' not in record.name:
					amount = record.amount_total
					record['total_signed_amount'] = -amount
					record['allocation_currency'] = record.currency_id.id


				else:
					record['total_signed_amount'] = record.amount_total

	
	def _get_amount_usd(self):
		for record in self:
			date = datetime.now().strftime('%Y-%m-%d')
			currency_id = record.currency_id
			company_id = record.company_id
			record['dollar_amount'] = record.total_signed_amount
			amount_total = record.total_signed_amount
			name = record.name
			partner_id = record.partner_id

			amount = 0
			if company_id:
				if record.invoice_date:
					date = record.invoice_date
				amount = currency_id._convert(amount_total,self.env.ref('base.USD'),company_id,date)

			if name[:2] == 'CR':
				record['dollar_amount'] = -amount

			elif name[:2] == 'RC':
				amount_total = -record.total_signed_amount
				receipt = self.env['account.payment'].search([('name','=',name),('partner_id','=',partner_id.id)],limit=1)
				date = datetime.today()
				if receipt.payment_date:
					date = receipt.payment_date
				amount = receipt.currency_id._convert(amount_total,self.env.ref('base.USD'),company_id,date)
				if receipt.amount_receipt > 0:
					record['dollar_amount'] = -amount

				else:
					record['dollar_amount'] = amount

			elif 'RF' in name:
				amount_total = record.total_signed_amount
				receipt = self.env['account.payment'].search([('name','=',name),('partner_id','=',partner_id.id)],limit=1)
				date = datetime.today()
				if receipt.payment_date:
					date = receipt.payment_date
				amount = receipt.currency_id._convert(amount_total,self.env.ref('base.USD'),company_id,date)
				record['dollar_amount'] = amount

			else:
				record['dollar_amount'] = amount


	@api.depends('name')
	def _compute_is_statement(self):
		for record in self:
			record['is_statement'] = False

			if 'RC' in record.name or 'RF' in record.name or 'SI' in record.name or 'CR' in record.name:
				record['is_statement'] = True

	def _compute_is_soa(self):
		for record in self:
			record['is_soa_statement'] = False

			if 'RC' in record.name or 'RF' in record.name or 'SI' in record.name or 'CR' in record.name:
				record['is_soa_statement'] = True




	"""def _compute_balance(self):
		for record in self:
			names = ['RC','RF','SI','CR']
			record['balance'] = record.amount_usd
			record['local_balance'] = record.total_signed_amount

			
			
			if isinstance(record.id, int):
				last_move = self.env['account.move'].search(['|','|','|',('name','ilike','RC'),('name','ilike','RF'),('name','ilike','SI'),('name','ilike','CR'),('partner_id','=',record.partner_id.id),('id','<',int(record.id))],order='id desc',limit=1)
				if last_move.is_soa_statement:
					last_move._compute_balance()
					if last_move:
						record['balance'] = record.amount_usd + last_move.balance
						record['local_balance'] = record.total_signed_amount + last_move.local_balance"""

	def _compute_balance(self):
		for record in self:
			record.balance = record.amount_usd
			record.local_balance = record.total_signed_amount
			if isinstance(record.id, int):
				moves = self.env['account.move'].search(['|','|','|',('name','ilike','RC'),('name','ilike','RF'),('name','ilike','SI'),('name','ilike','CR'),('partner_id','=',record.partner_id.id),('id','<',int(record.id))])
				if moves:
					record.balance = record.amount_usd + sum(moves.mapped('amount_usd'))
					record.local_balance = record.total_signed_amount + sum(moves.mapped('total_signed_amount'))










