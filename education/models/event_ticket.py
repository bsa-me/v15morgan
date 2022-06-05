from odoo import models, fields, api, _
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError

class EventTicket(models.Model):
    _inherit = "event.event.ticket"
    mapped_item_ids = fields.Many2many('product.template', string="Mapped Items")
    tax_ids = fields.Many2many('account.tax', string="Taxes")
    amount_taxed = fields.Float('Amount Taxed', compute='_compute_amount_taxed')
    currency_id = fields.Many2one(related='event_id.company_id.currency_id')
    ticket_company_id = fields.Many2one('res.company', string="Region", domain="[('is_region', '=', True)]")
    company_currency = fields.Many2one('res.currency',string='Main Currency',store=True)
    description = fields.Text()
    mapped_course_ids = fields.Many2many('course', string="Mapped Courses")
    course_ticket_ids = fields.Many2many('course.ticket.price', string="Mapped Tickets")
    origin_ticket_id = fields.Many2one('course.ticket.price',string='Origin Ticket',store=True)
    mrm_id = fields.Integer('MRM ID')   
    mrm_currency = fields.Many2one('res.currency') 


    @api.depends('name', 'event_id','ticket_company_id')
    def _compute_origin_ticket(self):
        for record in self:
            course = record.event_id.course_id
            company = record.ticket_company_id
            name = record.name
            course_ticket = self.env['course.ticket.price'].search([('name','=',name),('company_id','=',company.id),('course_id','=',course.id)])
            record['origin_ticket_id'] = course_ticket.id

    def get_website_price(self, website):
        price = self.sudo().company_currency._convert(self.price, website.currency_id, self.ticket_company_id, date.today())
        if self.tax_ids:
            price = self.sudo().tax_ids.compute_all(price)['total_included']

        if self.mapped_item_ids:
            for item in self.sudo().mapped_item_ids:
                item_price = self.env['company.price'].sudo().search([('product_tmpl_region_id','=',item.id),
                    ('company_id.parent_id','=',website.company_id.id),
                    ('price','>', 0)],limit=1).local_price
                
                item_price = website.company_id.tax_ids.sudo().compute_all(item_price)['total_included']

                price += item_price

        if self.course_ticket_ids:
            for ticket in self.sudo().course_ticket_ids:
                price += ticket.get_website_price(website)

        return price
    
    def _compute_amount_taxed(self):
        for ticket in self:
            if(ticket.tax_ids):
                ticket.amount_taxed = ticket.tax_ids.compute_all(ticket.price)['total_included']
            else:
                ticket.amount_taxed = ticket.price

    def _compute_currency(self):
        for record in self:
            if record.mrm_currency:
                record['company_currency'] = record.mrm_currency.id

            else:
                record['company_currency'] = record.ticket_company_id.currency_id.id


