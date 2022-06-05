# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    account_move_id = fields.Many2one('account.move','Invoice',copy=True)

    def _create_backorder(self):
        backorders = super(StockPicking, self)._create_backorder()
        for order in backorders:
            order.write({'account_move_id': order.backorder_id.account_move_id.id})