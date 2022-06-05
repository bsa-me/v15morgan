from odoo import models, fields, api
from datetime import datetime


class CompanyPrice(models.Model):
    _name = 'company.price'
    _description = 'Course Pricing/Company'
    ticket_ids = fields.One2many('course.ticket.price', 'ticket_id')
    course_id = fields.Many2one('course')
    course_region_id = fields.Many2one('course')
    product_tmpl_id = fields.Many2one('product.template','Product')
    product_tmpl_region_id = fields.Many2one('product.template','Product')
    name = fields.Char('Ticket Name')
    company_id = fields.Many2one(
        'res.company',
        string="Company"
    )
    tax_ids = fields.Many2many('account.tax',domain="[('company_id','=',company_id)]")
    deadline = fields.Integer('Sales End')
    price = fields.Float('Price')
    ticket_id = fields.Many2one('company.price')
    topic_id = fields.Many2one('course.topic')
    is_company = fields.Boolean('Is Company')
    local_price = fields.Float('Local Price', compute="_compute_local_price", store=False)
    currency_id = fields.Many2one('res.currency',default=lambda self: self.env.ref('base.USD').id)
    company_currency = fields.Many2one('res.currency',related='company_id.currency_id',string='Local Currency',store=True)
    override_default_price = fields.Float('Override Default Price')

    def write(self, vals):
        res = super(CompanyPrice, self).write(vals)
        date = datetime.now().strftime('%Y-%m-%d')
        price = 0
        override_default_price = self.override_default_price
        if 'override_default_price' in vals:
            override_default_price = vals['override_default_price']

        if override_default_price > 0:
            pricelist_items = self.env['product.pricelist.item'].search([('related_region_price_id','=',self.id)])
            for price_list_item in pricelist_items:
                price = self.env.ref('base.USD')._convert(override_default_price,price_list_item.pricelist_id.currency_id,self.company_id,date)
                price_list_item.write({'fixed_price': price})


        return res

    """def _get_tax_domain(self):
        if self.company_id:
            tax_ids = []
            taxes = self.env['account.tax'].search([('company_id', '=', self.company_id.id),('type_tax_use', '=', 'sale')])
            for tax in taxes:
                tax_ids.append(tax.id)

            for region in self.company_id.region_ids:
                related_taxes = self.env['account.tax'].search([('company_id', '=', region.id),('type_tax_use', '=', 'sale')])
                for related_tax in related_taxes:
                    tax_ids.append(related_tax.id)

            return [('id', 'in', tax_ids)]"""






    @api.depends('price')
    def _compute_local_price(self):
        date = datetime.now().strftime('%Y-%m-%d')
        for company_price in self:
            if(company_price.company_id):
                company_price.local_price = self.env.ref('base.USD')._convert(company_price.price,company_price.company_currency,company_price.company_id,date)
            else:
                company_price.local_price = 0
        
    @api.onchange('company_id')
    def _onchange_company(self):
        self._compute_local_price()
        val = {}
        domain = {}
        value = {}
        taxes = []
        taxes_parent = []
        available_taxes = []
        if(self.company_id):
            taxes = self.env['account.tax'].search(['|',('company_id', 'in', self.company_id.region_ids.ids),('company_id', '=', self.company_id.id),('type_tax_use', '=', 'sale')])
            for tax in taxes:
                available_taxes.append(tax.id)
            if(self.company_id.parent_id):
                taxes_parent = self.env['account.tax'].search(
                    [('company_id', '=', self.company_id.parent_id.id),
                    ('type_tax_use', '=', 'sale')])
                for tax in taxes_parent:
                	available_taxes.append(tax.id)

        
        domain['tax_ids'] = [('id', 'in', available_taxes)]
        val['domain'] = domain
        val['value'] = {'tax_ids': False}
        return val
        