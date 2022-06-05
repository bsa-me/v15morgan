from odoo import models,fields
from datetime import datetime


class ProductTemplate(models.Model):
    _inherit = 'account.move.line'
    amount_total = fields.Monetary(currency_field='company_currency_id',string='Total',compute="_compute_amounts")
    price_tax = fields.Monetary(currency_field='company_currency_id',string='Tax Amount',compute="_compute_amounts")
    tax_rate = fields.Char(compute="_compute_amounts",string='Tax Rate (%)')
    course_name = fields.Char()
    price_subtotal_currency = fields.Monetary(string='Price Subtotal',compute="_compute_amounts")
    amount_total_currency = fields.Monetary(string='Amount Total',compute="_compute_amounts")
    invoice_date = fields.Date(related="move_id.invoice_date",store=True)
    invoice_currency = fields.Many2one('res.currency',related="move_id.currency_id",store=True,string="Invoice Currency")
    parent_company = fields.Many2one('res.company',related="move_id.company_id.parent_id",store=True,string="Parent Company")
    other_inv_reference = fields.Char(related="move_id.other_inv_ref",store=True)
    line_updated = fields.Boolean()
    mrm_stock_id = fields.Char('Stock Adjustment - ID')
    mrm_stock_type = fields.Char('Stock Adjustment - Type')


    def _compute_amounts(self):
        for record in self:
            #date = record.move_id.invoice_date
            date = datetime.now().strftime('%Y-%m-%d')
            usd = self.env.ref('base.USD')
            invoice_currency = record.move_id.currency_id
            rate = self.env['res.currency']._get_conversion_rate(usd, invoice_currency, record.move_id.company_id, date)

            price = record.price_unit * (1 - (record.discount or 0.0) / 100.0)
            taxes = record.tax_ids.compute_all(price, record.move_id.currency_id, record.quantity, product=record.product_id, partner=record.move_id.partner_id)
            record['amount_total'] = taxes['total_included']



            amount_total_currency = taxes['total_included']
            price_subtotal_currency = taxes['total_excluded']

            if record.move_id.type == 'out_refund':
                amount_total_currency = -taxes['total_included']
                price_subtotal_currency = -taxes['total_excluded']

            if record.move_id.currency_id == usd:
                amount_total_currency = amount_total_currency * rate
                price_subtotal_currency = price_subtotal_currency * rate

            record['amount_total_currency'] = amount_total_currency
            record['price_subtotal_currency'] = price_subtotal_currency

            price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
            if record.move_id.type == 'out_refund':
                price_tax = -sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

            if record.move_id.currency_id == usd:
                price_tax = price_tax * rate


            record['price_tax'] = price_tax
            rates = record.tax_ids.mapped('amount')
            record['tax_rate'] = ' '.join([str(rate) for rate in rates])
            



    _sql_constraints = [
    (
        'check_credit_debit',
        'CHECK(1=1)',
        'Wrong credit or debit value in accounting entry !'
        ),
    (
        'check_amount_currency_balance_sign',
        'CHECK(1=1)',
        "The amount expressed in the secondary currency must be positive when account is debited and negative when account is credited. Moreover, the currency field has to be left empty when the amount is expressed in the company currency."
        ),
    ]
    
  
  
        
