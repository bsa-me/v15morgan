from odoo import models, fields, api, _
from datetime import datetime
from datetime import date

class CourseTicketPrice(models.Model):
    _name ='course.ticket.price'
    _description = 'Course Ticket Price'
    name = fields.Char('Ticket Name')
    company_id = fields.Many2one('res.company', string="Region", domain="[('is_region', '=', True)]")
    tax_ids = fields.Many2many('account.tax', widget='many2many_tags')
    deadline = fields.Integer('Sales End (Before event start date)')
    price = fields.Float('Price')
    ticket_id = fields.Many2one('company.price')
    mapped_item_ids = fields.Many2many('product.template', string="Mapped Items")
    domain = fields.Char('Domain')
    currency_id = fields.Many2one('res.currency',default=lambda self: self.env.ref('base.USD').id)
    company_currency = fields.Many2one('res.currency',related='company_id.currency_id',string='Local Currency',store=True)
    is_region = fields.Boolean(related='company_id.is_region')
    local_price = fields.Float('Local Price', compute="_compute_local_price", store=False)
    course_id = fields.Many2one('course',related="ticket_id.course_region_id",store=True)
    
    @api.depends('price')
    def _compute_local_price(self):
        date = datetime.now().strftime('%Y-%m-%d')
        for course_ticket in self:
            if(course_ticket.company_id):
                course_ticket.local_price = self.env.ref('base.USD')._convert(course_ticket.price,course_ticket.company_currency,course_ticket.company_id,date)
            else:
                course_ticket.local_price = 0

    def get_website_price(self, website):
        price = self.env.ref('base.USD')._convert(self.price, website.currency_id, website.company_id, date.today())
        if self.ticket_id.tax_ids:
            price = self.sudo().ticket_id.tax_ids.compute_all(price)['total_included']

        if self.mapped_item_ids:
            for item in self.sudo().mapped_item_ids:
                item_price = self.env['company.price'].sudo().search([('product_tmpl_region_id','=',item.id),
                    ('company_id.parent_id','=',website.company_id.id),
                    ('price','>', 0)],limit=1).local_price

                item_price = website.company_id.tax_ids.sudo().compute_all(item_price)['total_included']

                price += item_price

        return price