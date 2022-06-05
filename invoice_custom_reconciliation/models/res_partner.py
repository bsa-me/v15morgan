# -*- coding: utf-8 -*-

from odoo import api, fields, models

class Partner(models.Model):
  _inherit='res.partner'

  future_payments = fields.One2many('account.move.line','partner_id',string='Future Payments',domain=lambda self:[('is_future_payment','=',True),('line_type','=','out_invoice')])
  future_payment_ids = fields.One2many('morgan.future.payment','partner_id')
  
