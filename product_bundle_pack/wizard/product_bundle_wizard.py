# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime


class bi_wizard_product_bundle(models.TransientModel):
    _name = 'wizard.product.bundle.bi'

    product_id = fields.Many2one('product.product',string='Bundle',required=True)
    product_qty = fields.Integer('Quantity',required=True ,default=1)
    product_price = fields.Float(string="Price")
    pack_ids = fields.One2many('product.pack', related='product_id.pack_ids', string="Select Products")
    
    
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
                            })
                    else:
                        if descriptions == '':
                            descriptions += item.product_id.name

                        else:
                            descriptions = descriptions + ' - ' + (item.product_id.name)

                test = self.env['sale.order.line'].create({'order_id':self._context['active_id'],
                    'sequence': 1,
                    'product_id':pack.product_id.id,
                    'name':descriptions,
                    'price_unit':self.product_price,
                    'product_uom':pack.product_id.uom_id.id,
                    'product_uom_qty': self.product_qty
                    })
            order.write({'name': 'New'})

        return True 

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            order = self.env['sale.order'].browse(self._context['active_id'])
            pricelist = order.pricelist_id

            price = pricelist.get_product_price(self.product_id, self.product_qty, order.partner_id, date=False, uom_id=False)
            self.product_price = price
        else:
            pass                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       