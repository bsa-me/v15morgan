from odoo import api, fields, models


class EventSales(models.Model):
    _name = 'event.sales'
    event_id = fields.Many2one('event.event','Event')
    total_before_tax = fields.Monetary('Total Sales Before Tax')
    total_after_tax = fields.Monetary('Total Sales After Tax')
    company_id = fields.Many2one('res.company','Region')
    currency_id = fields.Many2one('res.currency','Currency',related="company_id.currency_id",store=False)
    event_sale_details_ids = fields.One2many('event.sales.details','event_sale_id')

class EventSalesDetails(models.Model):
    _name = 'event.sales.details'
    event_sale_id = fields.Many2one('event.sales')
    account_move_line_id = fields.Many2one('account.move.line','Related Invoice Line')
    product_id = fields.Many2one('product.product',store=True,related="account_move_line_id.product_id")
    account_move_id = fields.Many2one(related='account_move_line_id.move_id',store=True,string='Related Invoice')
    invoice_currency = fields.Many2one('res.currency',related='account_move_line_id.move_id.currency_id')
    price_subtotal_currency = fields.Monetary(currency_field='invoice_currency')
    amount_total = fields.Monetary(currency_field='invoice_currency')





