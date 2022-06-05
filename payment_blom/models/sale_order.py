# coding: utf-8

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    blom_order_ref = fields.Char('Blom ref')