# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import api, fields, models, _


class bi_statement_line(models.Model):
	
	_name = 'bi.statement.line'
	_description = "Customer Statement Line"
	
	
	company_id = fields.Many2one('res.company', string='Company',related="invoice_id.company_id",store=True)
	partner_id = fields.Many2one('res.partner', string='Customer')
	name = fields.Char('Name') 
	invoice_date = fields.Date('Invoice Date')
	invoice_date_due = fields.Date('Due Date')
	# number = fields.Char('Number')
	result = fields.Float("Balance")
	amount_total = fields.Float("Invoices/Debits")
	credit_amount = fields.Float("Payments/Credits")

	state = fields.Selection(selection=[
			('draft', 'Draft'),
			('posted', 'Posted'),
			('cancel', 'Cancelled')
		], string='Status', required=True, readonly=True, copy=False, tracking=True,
		default='draft')
	invoice_id = fields.Many2one('account.move', String='Invoice')
	payment_id = fields.Many2one('account.payment', String='Payment')
	currency_id = fields.Many2one(related='invoice_id.currency_id')
	amount_total_signed = fields.Monetary(related='invoice_id.amount_total_signed', currency_field='currency_id',)
	amount_residual = fields.Monetary(related='invoice_id.amount_residual')
	amount_residual_signed = fields.Monetary(related='invoice_id.amount_residual_signed', currency_field='currency_id',)
	total_signed_amount = fields.Float(related="invoice_id.total_signed_amount",string='Amount')
	balance = fields.Float(related="invoice_id.balance",string='Balance')
	document_id = fields.Integer(related="invoice_id.id",string='ID',store=True)
	is_payment_move = fields.Boolean(related="invoice_id.is_payment_move")
	
	
	
	
	
	_order = 'invoice_date'
	
	
	
class bi_vendor_statement_line(models.Model):
	
	_name = 'bi.vendor.statement.line'
	_description = "Vendor Statement Line"
	
	
	company_id = fields.Many2one('res.company', string='Company')
	partner_id = fields.Many2one('res.partner', string='Customer')
	name = fields.Char('Name') 
	invoice_date = fields.Date('Invoice Date')
	invoice_date_due = fields.Date('Due Date')
	# number = fields.Char('Number')
	result = fields.Float("Balance")
	amount_total = fields.Float("Invoices/Debits")
	credit_amount = fields.Float("Payments/Credits")
	state = fields.Selection(selection=[
			('draft', 'Draft'),
			('posted', 'Posted'),
			('cancel', 'Cancelled')
		], string='Status', required=True, readonly=True, copy=False, tracking=True,
		default='draft')
	invoice_id = fields.Many2one('account.move', String='Invoice')
	payment_id = fields.Many2one('account.payment', String='Payment')
	currency_id = fields.Many2one(related='invoice_id.currency_id')
	amount_total_signed = fields.Monetary(related='invoice_id.amount_total_signed', currency_field='currency_id',)
	amount_residual = fields.Monetary(related='invoice_id.amount_residual')
	amount_residual_signed = fields.Monetary(related='invoice_id.amount_residual_signed', currency_field='currency_id',)
	
	
	
	
	
	_order = 'invoice_date'
	
