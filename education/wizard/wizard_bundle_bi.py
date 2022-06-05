# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime


class WizardBudnleBi(models.TransientModel):
    _inherit = 'wizard.product.bundle.bi'
    product_ids = fields.Many2many('product.product',string='Products')
    term_id = fields.Many2one('term',string='Term',required=True)

    def button_add_product_bundle_bi(self):
    	for pack in self:
    		pricelist = self.env['sale.order'].browse(self._context['active_id']).pricelist_id
    		date = datetime.now().strftime('%Y-%m-%d')
    		order = self.env['sale.order'].browse(self._context['active_id'])
    		currency = order.currency_id
    		currencyUsd = self.env.ref('base.USD')
    		rate = currency._get_conversion_rate(currencyUsd,currency,order.company_id,date)

    		if pack.product_id.is_pack:
    			descriptions = ''
    			for item in pack.product_id.pack_ids:
    				price_unit = False
    				product_uom_qty = False
    				if(item.show_on_invoice):
    					price_unit = pricelist.get_product_price(item.product_id, 1, order.partner_id, date=False, uom_id=False)
    					product_uom_qty = item.qty_uom * self.product_qty
    					item_line = self.env['sale.order.line'].create({'order_id':self._context['active_id'],
    						'sequence': 2,
    						'product_id':item.product_id.id,
    						'name':item.product_id.name,
    						'price_unit': False,
    						'show_on_invoice': item.show_on_invoice,
    						'product_uom':item.product_id.uom_id.id,
    						'product_uom_qty': product_uom_qty,
    						'term_id': self.term_id.id
    						})
    				else:
    					descriptions = descriptions + ' - ' + (item.product_id.name)

    			test = self.env['sale.order.line'].create({'order_id':self._context['active_id'],
    				'sequence': 1,
    				'product_id':pack.product_id.id,
    				'name':descriptions,
    				'price_unit':self.product_price,
    				'product_uom':pack.product_id.uom_id.id,
    				'product_uom_qty': self.product_qty,
    				'term_id': self.term_id.id
    				})

    		order.write({'name': 'New'})

    	return True