# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re

class AccountMoveLine(models.Model):
  _inherit='account.move.line'

  is_future_payment = fields.Boolean()
  amount_usd = fields.Float('Amount($)',compute="compute_usd")
  currency_usd = fields.Many2one('res.currency',compute="compute_usd")
  parent_company_id = fields.Many2one(related='company_id.parent_id',string='Billing Company')
  line_type = fields.Selection(related='move_id.move_type')

  def _check_reconciliation(self):
    for line in self:
      if line.matched_debit_ids or line.matched_credit_ids:
        return


  """@api.model
  def create(self, vals):
    move = self.env['account.move'].browse(vals['move_id'])
    company = move.company_id
    if company != self.env.company:
      if 'credit' in vals:
        if vals['credit'] > 0:
          if move.type == 'out_invoice':
            vals['account_id'] = self.env['account.account'].search([('company_id','=', company.id),('code','=','400000'),('name','=','Product Sales')],limit=1).id

          elif move.type == 'out_refund':
            vals['account_id'] = self.env['account.account'].search([('company_id','=', company.id),('code','=','121000'),('name','=','Account Receivable')],limit=1).id

      if 'debit' in vals:
        if vals['debit'] > 0:
          if move.type == 'out_refund':
            vals['account_id'] = self.env['account.account'].search([('company_id','=', company.id),('code','=','121000'),('name','=','Account Receivable')],limit=1).id

          elif move.type == 'out_invoice':
            vals['account_id'] = self.env['account.account'].search([('company_id','=', company.id),('code','=','400000'),('name','=','Product Sales')],limit=1).id

      if vals['credit'] == 0 and vals['debit'] == 0:
        if move.type == 'out_invoice':
          vals['account_id'] = self.env['account.account'].search([('company_id','=', company.id),('code','=','400000'),('name','=','Product Sales')],limit=1).id

        elif move.type == 'out_refund':
          vals['account_id'] = self.env['account.account'].search([('company_id','=', company.id),('code','=','121000'),('name','=','Account Receivable')],limit=1).id

    return super(AccountMoveLine, self).create(vals)"""


    


  def compute_usd(self):
  	date = datetime.now().strftime('%Y-%m-%d')
  	for record in self:
  		record.currency_usd = self.env.ref('base.USD').id
  		record.amount_usd = record.company_currency_id._convert(record.debit,record.env.ref('base.USD'),record.company_id,date)



  @api.depends('debit', 'credit', 'account_id', 'amount_currency', 'currency_id', 'matched_debit_ids', 'matched_credit_ids', 'matched_debit_ids.amount', 'matched_credit_ids.amount', 'move_id.state', 'company_id')
  def _amount_residual(self):
    for line in self:
      if not line.account_id.reconcile and line.account_id.internal_type != 'liquidity':
        line.reconciled = False
        line.amount_residual = 0
        line.amount_residual_currency = 0
        continue

      amount = abs(line.debit - line.credit)
      amount_residual_currency = abs(line.amount_currency) or 0.0
      sign = 1 if (line.debit - line.credit) > 0 else -1
      if not line.debit and not line.credit and line.amount_currency and line.currency_id:
        sign = 1 if float_compare(line.amount_currency, 0, precision_rounding=line.currency_id.rounding) == 1 else -1

      for partial_line in (line.matched_debit_ids + line.matched_credit_ids):
        sign_partial_line = sign if partial_line.credit_move_id == line else (-1 * sign)

        amount += sign_partial_line * partial_line.amount
        if line.currency_id and line.amount_currency:
          if partial_line.currency_id and partial_line.currency_id == line.currency_id:
            amount_residual_currency += sign_partial_line * partial_line.amount_currency
          else:
            if line.balance and line.amount_currency:
              rate = line.amount_currency / line.balance
            else:
              date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
              rate = line.currency_id.with_context(date=date).rate
            amount_residual_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)

      reconciled = False
      digits_rounding_precision = line.company_id.currency_id.rounding
      if (line.matched_debit_ids or line.matched_credit_ids) and float_is_zero(amount, precision_rounding=digits_rounding_precision):
        if line.currency_id and line.amount_currency:
          if float_is_zero(amount_residual_currency, precision_rounding=line.currency_id.rounding):
            reconciled = True
        else:
          reconciled = True

      line.reconciled = reconciled
      line.amount_residual = line.move_id.company_id.currency_id.round(amount * sign) if line.move_id.company_id else amount * sign
      line.amount_residual_currency = line.currency_id and line.currency_id.round(amount_residual_currency * sign) or 0.0


