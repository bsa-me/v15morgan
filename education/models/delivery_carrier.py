from odoo import models, fields, _
import datetime

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    product_ids = fields.One2many('shipping.price', 'carrier_id', string="Products")
    delivery_type = fields.Selection(selection_add=[('products', 'Based on Products')],ondelete={'products': 'cascade'})


    
    
    
    def products_rate_shipment(self, order):
        carrier = self._match_address(order.partner_shipping_id)
        price_list = order.pricelist_id
        res = {}
        if not carrier:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error: this delivery method is not available for this address.'),
                    'warning_message': False}
        else:
            total_price = 0
            date = datetime.datetime.now().strftime('%Y-%m-%d')


            region_ids = [order.company_id.id]
            if order.company_id.region_ids:
                for region in order.company_id.region_ids:
                    region_ids.append(region.id)

            elif order.company_id.parent_id:
                region_ids.append(order.company_id.parent_id.id)

            for line in order.order_line:
                #Get Pricing on first region
                
                shipping_cost = self.env['shipping.price'].sudo().search([
                    ('product_id', '=', line.product_id.product_tmpl_id.id),
                    ('company_id', 'in', region_ids),
                    ('carrier_id', '=', self.id)], limit=1)

                if not shipping_cost:
                    shipping_cost = self.env['shipping.price'].sudo().search([
                        ('product_id.name', '=', line.product_id.product_tmpl_id.name),
                        ('company_id', 'in', region_ids),
                        ('carrier_id', '=', self.id)], limit=1)

                if(shipping_cost):
                    from_currency = price_list.currency_id
                    to_currency = shipping_cost.x_currency_id
                    total_price += to_currency.compute(shipping_cost.price, from_currency) * line.product_uom_qty
                    #total_price += shipping_cost.x_currency_id._convert(shipping_cost.price, price_list.currency_id, order.company_id, date) * line.product_uom_qty

            res['price'] = total_price
            res = {
            'success': True,
            'price': total_price,
            'error_message': False,
            'warning_message': False,
            'carrier_price': total_price
            }
            if res['success'] and total_price == 0:
                res['warning_message'] = _('The shipping is free since none of the items is mapped to a shipping')
                
            #if res['success'] and self.free_over and order._compute_amount_total_without_delivery() >= self.amount:
            #    res['warning_message'] = _('The shipping is free since the order amount exceeds %.2f.') % (self.amount)
            #    res['price'] = 0.0
            return res