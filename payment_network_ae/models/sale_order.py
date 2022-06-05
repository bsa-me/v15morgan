# coding: utf-8

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    network_ae_order_ref = fields.Char('Network AE ref')
