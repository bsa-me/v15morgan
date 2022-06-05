# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re
from datetime import datetime

class AccountMove(models.Model):
  _inherit='account.move'
  future_payment_ids = fields.One2many('morgan.future.payment','invoice_id',string='Payments')
  total_fp_amount = fields.Float()
  allocation = fields.Char(compute="compute_allocation",string='Allocation')
  over_due_payment = fields.Float(compute="compute_over_due_payment",store=True)
  is_payment = fields.Boolean(compute="_compute_payment")
  allocated = fields.Boolean(compute="_compute_allocate")
  payment_ids = fields.Many2many('account.payment','account_invoice_payment_rel','invoice_id','payment_id',copy=False, readonly=True,string='Receipts')
  amount_untaxed_sign = fields.Monetary(compute="_compute_amount_sign")
  amount_tax_sign = fields.Monetary(compute="_compute_amount_sign")
  amount_total_sign = fields.Monetary(compute="_compute_amount_sign")
  fp_schedule = fields.Float('Amount to be scheduled')
  register_payment_line_ids = fields.One2many('register.payment.line','move_id',string='Payment line ids')



  def _compute_amount_sign(self):
    for record in self:
      record['amount_untaxed_sign'] = record.amount_untaxed
      record['amount_tax_sign'] = record.amount_tax
      record['amount_total_sign'] = record.amount_total

      if record.type == 'out_refund':
        record['amount_untaxed_sign'] = -record.amount_untaxed
        record['amount_tax_sign'] = -record.amount_tax
        record['amount_total_sign'] = -record.amount_total



  def _compute_currency_usd(self):
    for record in self:
      record['currency_usd'] = self.env.ref('base.USD').id

  def _compute_payment(self):
    for record in self:
      record['is_payment'] = False
      if record.name[:2] == 'RC' or record.name[:2] == 'RF':
        record['is_payment'] = True

  def _compute_allocate(self):
    for record in self:
      record['allocated'] = False
      if record.is_payment:
        payment = self.env['account.payment'].search([('name','=',record.name),('partner_id','=',record.partner_id.id),('company_id','=',record.company_id.id)],limit=1)
        if payment.invoice_ids and payment.state == 'reconciled':
          record['allocated'] = True

  def _recompute_payment_terms_lines(self):
    self.ensure_one()
    in_draft_mode = self != self._origin
    today = fields.Date.context_today(self)

    def _get_payment_terms_computation_date(self):
      if self.invoice_payment_term_id:
        return self.invoice_date or today
      else:
        return self.invoice_date_due or self.invoice_date or today



    def _get_payment_terms_account(self, payment_terms_lines):
      if payment_terms_lines:
        return payment_terms_lines[0].account_id

      elif self.partner_id:
        if self.is_sale_document(include_receipts=True):
          return self.partner_id.property_account_receivable_id

        else:
          return self.partner_id.property_account_payable_id

      else:
        domain = [
        ('company_id', '=', self.company_id.id),
        ('internal_type', '=', 'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
        ]

        return self.env['account.account'].search(domain, limit=1)

    def _compute_payment_terms(self, date, total_balance, total_amount_currency):
      if self.invoice_payment_term_id:
        to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date, currency=self.currency_id)
        if self.currency_id != self.company_id.currency_id:
          to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date, currency=self.currency_id)
          return [(b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency)]

        else:
          return [(b[0], b[1], 0.0) for b in to_compute]

      else:
        return [(fields.Date.to_string(date), total_balance, total_amount_currency)]

    def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
      existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
      existing_terms_lines_index = 0
      new_terms_lines = self.env['account.move.line']
      for date_maturity, balance, amount_currency in to_compute:
        if self.journal_id.company_id.currency_id.is_zero(balance) and len(to_compute) > 1:
          continue


        if existing_terms_lines_index < len(existing_terms_lines):
          candidate = existing_terms_lines[existing_terms_lines_index]
          existing_terms_lines_index += 1
          candidate.update({
            'date_maturity': date_maturity,
            'amount_currency': -amount_currency,
            'debit': balance < 0.0 and -balance or 0.0,
            'credit': balance > 0.0 and balance or 0.0,

          })

        else:
          company_sequence = False
          parent_sequence = False
          name = ''
          code = 'account.move.line'
          ref = 'FP-'

          if(not self.company_id.document_sequence):
            company_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.id),('code','=',code),('prefix','=','FP')],limit=1)
            name = ref + self.company_id.code+'-'+str(company_sequence.number)
            company_sequence.write({'number': company_sequence.number + 1})

          else:
            parent_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.parent_id.id),('code','=',code),('prefix','=','FP')],limit=1)
            if(parent_sequence):
              name = ref+self.company_id.parent_id.code+'-'+str(parent_sequence.number)
              parent_sequence.write({'number': parent_sequence.number + 1})

          create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
          candidate = create_method({
            'name': name,
            'debit': balance < 0.0 and -balance or 0.0,
            'credit': balance > 0.0 and balance or 0.0,
            'quantity': 1.0,
            'amount_currency': -amount_currency,
            'date_maturity': date_maturity,
            'move_id': self.id,
            'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
            'account_id': account.id,
            'partner_id': self.commercial_partner_id.id,
            'exclude_from_invoice_tab': True,
            'is_future_payment': True,
            })




        new_terms_lines += candidate
        if in_draft_mode:
          candidate._onchange_amount_currency()
          candidate._onchange_balance()

      return new_terms_lines

    existing_terms_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
    others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
    total_balance = sum(others_lines.mapped('balance'))
    total_amount_currency = sum(others_lines.mapped('amount_currency'))

    if not others_lines:
      self.line_ids -= existing_terms_lines
      return

    computation_date = _get_payment_terms_computation_date(self)
    account = _get_payment_terms_account(self, existing_terms_lines)
    to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
    new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

    self.line_ids -= existing_terms_lines - new_terms_lines

    if new_terms_lines:
      self.invoice_payment_ref = new_terms_lines[-1].name or ''
      self.invoice_date_due = new_terms_lines[-1].date_maturity

  def action_post(self):
    self.action_refund_fp()
    res = super(AccountMove, self).action_post()
    date = datetime.now().strftime('%Y-%m-%d')
    move_lines = self.env['account.move.line'].search([('move_id','in',self.ids),('is_future_payment','=',1)])
    self.env['morgan.future.payment'].search([('invoice_id','in',self.ids),('from_mrm','=',False)]).unlink()
    if self.type == 'out_invoice':
      if not self.future_payment_ids:
        for move_line in move_lines:
          #raise UserError(move_line.company_currency_id.name)
          amount = move_line.company_currency_id._convert(move_line.debit,self.currency_id,self.company_id,date)
          self.env['morgan.future.payment'].create({
            'name': move_line.name,
            'amount': amount,
            'due_amount': amount,
            'region_id': move_line.company_id.id,
            'invoice_id': self.ids[0],
            'due_date': move_line.date_maturity,
            'partner_id': self.partner_id.id,
            })

    return res


  @api.onchange('future_payment_ids')
  def onchange_future_payment(self):
    total_amount = 0
    for fp in self.future_payment_ids:
      total_amount = total_amount + fp.amount

    self.total_fp_amount = total_amount
    self.fp_schedule = round(self.amount_total, 2) - total_amount

  @api.constrains('future_payment_ids')
  def check_fp_amount(self):
    if self.state == 'posted':
      if round(self.total_fp_amount,2) != round(self.amount_total,2):
        raise ValidationError('the total amount of the fps should be equal to the amount of the invoice')

  def button_draft(self):
    #future_payments = self.env['morgan.future.payment'].search([('invoice_id','in',self.ids),('from_mrm','=',False)]).unlink()
    #for fp in future_payments:
      #move_line = self.env['account.move.line'].search([('name','=',fp.name),('move_id','=',fp.invoice_id.id)]).unlink()
      #fp.unlink()
    res = super(AccountMove, self).button_draft()


  def action_refund_fp(self):
    date = datetime.now().strftime('%Y-%m-%d')
    if(self.type == 'out_refund'):
      amount = self.amount_total

      total_amount = 0
      for line in self.invoice_line_ids:
        total_amount = total_amount + line.price_subtotal

      total_refunds = 0
      refunds = self.env['account.move'].search([('reversed_entry_id','=',self.reversed_entry_id.id),('state','=','posted')])
      for refund in refunds:
        if(refund.id != self.id):
          total_refunds = total_refunds + refund.amount_total

      due_amount = self.reversed_entry_id.amount_total - total_refunds

      #raise UserError(total_refunds)

      if(amount > due_amount):
        raise UserError("You can't validate a credit note with an amount greater than the due amount of its related invoice, please adjust the invoice lines!")

      if(len(refunds) == 1):
        if self.reversed_entry_id.amount_total < total_amount:
          raise UserError("You can't validate a credit note with an amount greater than the due amount of its related invoice, please adjust the invoice lines!")

      amount = self.amount_total
      move_lines = self.env['account.move.line'].search([('move_id','=',self.reversed_entry_id.id),('is_future_payment','=',1)],order='date_maturity asc')
      for line in move_lines:
        if amount > 0:
          due_amount = line.amount_residual
          if amount > due_amount:
            #raise UserError(due_amount)
            partial_reconcile = self.env['account.partial.reconcile'].create({
              'debit_move_id': line.id,
              'credit_move_id': self.env['account.move.line'].search([('move_id','=',self.id),('debit','>',0)],order='debit',limit=1).id,
              'company_id': self.company_id.id,
              'amount': line.company_currency_id._convert(due_amount,line.move_id.currency_id,line.company_id,date),
              'is_refund': 1,
          })
            #raise UserError(partial_reconcile.amount)
          else:
            #raise UserError(due_amount - amount)
            partial_reconcile = self.env['account.partial.reconcile'].create({
              'debit_move_id': line.id,
              'credit_move_id': self.env['account.move.line'].search([('move_id','=',self.id),('debit','>',0)],order='debit',limit=1).id,
              'company_id': self.company_id.id,
              'amount': line.move_id.currency_id._convert(amount,line.company_currency_id,line.company_id,date),
              'is_refund': 1,
          })

          amount = amount - due_amount
          #raise UserError(amount)
          if amount <= 0:
            amount = 0


      mrm_future_payment = self.env['morgan.future.payment'].search([('invoice_id','=',self.reversed_entry_id.id),('from_mrm','=',True),('due_amount','>',0)],order='due_date')
      amount = self.amount_total
      if amount > 0:
        for fp in mrm_future_payment:
          amount = fp.due_amount - amount
          if amount >= 0:
            fp.write({'due_amount': amount})
            break

          else:
            fp.write({'due_amount': 0})
            amount = -amount
      #self.reversed_entry_id.compute_over_due_payment()

  def compute_allocation(self):
    for record in self:
      number = ''
      index = 0
      if 'RC' in record.name or 'RF' in record.name:
        receipt = self.env['account.payment'].search([('name','=',record.name)],limit=1)
        for inv in receipt.invoice_ids:
          number = number + inv.name
          while (index < (len(receipt.invoice_ids) - 1)):
            number = number + '/'
            index = index + 1

      elif 'CR' in record.name:
        number = record.reversed_entry_id.name

      record['allocation'] = number

  def compute_over_due_payment(self):
    for record in self:
      total_payments = 0
      date = datetime.now().strftime('%Y-%m-%d')
      """for line in record.line_ids:
        credit_moves = self.env['account.partial.reconcile'].search([('debit_move_id','=',line.id),('credit_move_id.credit','>',0)])
        for credit_move in credit_moves:
          total_payments = total_payments - credit_move.amount"""


      payments = self.payment_ids
      for payment in payments:
        amount = payment.amount
        payment_amount = payment.currency_id._convert(amount, record.currency_id, record.company_id, date)
        if payment.name and 'RC' in payment.name:
          total_payments = total_payments + payment_amount

        elif payment.name and 'RF' in payment.name:
          total_payments = total_payments - payment_amount




      for credit_note in record.reversal_move_id:
        total_payments = total_payments + credit_note.amount_total

      record['over_due_payment'] = record.amount_total - total_payments




  def write(self, vals):
    #update due amount for future payments, either the created from odoo or from mrm
    date = datetime.now().strftime('%Y-%m-%d')
    for record in self.line_ids:
      future_payment = self.env['morgan.future.payment'].search([('name','=',record.name),('invoice_id','=',record.move_id.id),('from_mrm','=',False)],limit=1)
      if future_payment:
        amount = float(record.amount_residual)
        if record.company_currency_id != record.move_id.currency_id:
          amount = record.company_currency_id._convert(float(record.amount_residual),record.move_id.currency_id,record.company_id,date)

        self.env.cr.execute("update morgan_future_payment set due_amount = "+str(amount) + " where id = "+str(future_payment.id))

    return super(AccountMove, self).write(vals)


  def allocate_payment(self):
    if self.is_payment:
        if not self.allocated:
            payment = self.env['account.payment'].search([('name','=',self.name),('company_id','=',self.company_id.id)],limit=1)
            if payment:
                return payment.open_register_payment_popup_form()

        else:
            raise ValidationError('This receipt is already allocated!')


  def open_payment(self):
    payment = self.env['account.payment'].search([('name','=',self.name),('partner_id','=',self.partner_id.id),('company_id','=',self.company_id.id)],limit=1)
    action = self.env.ref('account.action_account_payments').read()[0]
    view_id = self.env.ref('account.view_account_payment_form').id
    action['view_id'] = view_id
    action['domain'] = [('id','=',payment.id)]
    action['res_id'] = payment.id
    action['views'] = [(view_id, 'form')]
    action['view_mode'] = 'form'
    return action


  def reallocate(self):
    payment = self.env['account.payment'].search([('name','=',self.name),('amount','=',self.amount_total),('company_id','=',self.company_id.id)],limit=1)
    if not payment:
      payment = self.env['account.payment'].search([('name','=',self.name),('amount','=',self.amount_total_signed),('company_id','=',self.company_id.id)],limit=1)
    if payment:
      if payment.partial_reconcile_ids:
        for partial in payment.partial_reconcile_ids:
          partial.unlink()

      payment.write({'invoice_ids': False})

      if not payment.partial_reconcile_ids:
        return payment.open_register_payment_popup_form()

  def action_future_payment_sent(self):
    self.ensure_one()
    template = self.env.ref('invoice_custom_reconciliation.email_template_fp', raise_if_not_found=False)
    template.send_mail(self.ids[0],force_send=True)
    return self.env.ref('invoice_custom_reconciliation.report_future_payment_document').report_action(self)
