# -*- coding: utf-8 -*-

from odoo import api, fields, models

class BiStatementLine(models.Model):
  _inherit='bi.statement.line'
  allocation = fields.Char(related="invoice_id.allocation",string='Allocation')