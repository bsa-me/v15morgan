from odoo import api, fields, models
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order.line'
    discount_id = fields.Many2one('sale.order.discount','Discount(%)')
    discount_ids = fields.Many2many('sale.order.discount',string='Discounts')

    @api.onchange('discount_id')
    def _onchange_discount_id(self):
        self.discount = 0
        if self.discount_id:
            self.discount = self.discount_id.discount_percentage

    @api.onchange('discount_ids')
    def _onchange_discount_ids(self):
    	self.discount = 0
    	if self.discount_ids:
    		total_discount = 0
    		total = self.price_subtotal
    		for discount in self.discount_ids:
    			amount_discounted = discount.discount_percentage * total / 100
    			total = total - amount_discounted
    			total_discount += amount_discounted

	    	self.discount = total_discount * 100 / self.price_subtotal if self.price_subtotal > 0 else 0




