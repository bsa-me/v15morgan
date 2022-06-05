from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError
from datetime import datetime


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    track_id = fields.Many2one('event.track')
    event_id = fields.Many2one('event.event', string='Event')
    term_id = fields.Many2one('term', string='Term')
    session_id = fields.Many2one('event.track', string='Session')
    course_id = fields.Many2one('course','Course')
    """event_track_seats_availability = fields.Selection(
        related='session_id.event_id.seats_availability',
        string='Seats Availavility',
        readonly=True
    )
    event_session_seats_availability = fields.Selection(
        related='event_id.seats_availability',
        string='Seats Availavility',
        readonly=True,
    )"""
    event_session_seats_available = fields.Integer(
        related='event_id.seats_available',
        string='Available Seats',
        readonly=True,
    )
    event_sessions_count = fields.Integer(
        comodel_name='event.track',
        related='event_id.track_count',
        readonly=True,
    )
    registration_ids = fields.One2many(
        'event.registration', 
        'sale_order_line_id',
        string='Attendees',
        readonly=True)

    is_discountable = fields.Boolean(related="product_id.product_tmpl_id.is_discountable",string='Is Discountable')
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    related_order_line_id = fields.Many2one('sale.order.line')
    product_categ_id = fields.Many2one('product.category',related="product_id.categ_id",store=True)
    study_format = fields.Many2one('event.type',related="event_id.event_type_id",store=True)
    origin_ticket_id = fields.Many2one('course.ticket.price')

    @api.onchange('track_id', 'session_id')
    def onchange_track_id(self):
        val = {}
        #if not self.order_id._session_seats_available():
        #    raise ValidationError(_(
        #        "Not enough seats. Change quantity or session"))
        if self.session_id:
            tax_ids = []
            for tax in self.session_id.tax_ids:
                tax_ids.append(tax.id)
            val['value'] = {
                'name': self.session_id.display_name + '\r' + str(self.session_id.date),
                'price_unit': self.session_id.price,
                'tax_id': [(6, 0, tax_ids)]
            }
        return val
            
    
            
    @api.onchange()
    def product_uom_change(self):
        if not self.order_id._track_seats_available():
            raise ValidationError(
                _("Not enough seats. Change quantity or session"))
            return super().product_uom_change()

    @api.onchange('event_id')
    def _onchange_event_id(self):
        if self.event_sessions_count == 1:
            self.track_id = self.event_id.track_ids[0]
            return super()._onchange_event_id()
            
            def get_sale_order_line_multiline_description_sale(self, product):
                name = super().get_sale_order_line_multiline_description_sale(product)
                if self.event_ticket_id and self.track_id:
                    name += '\n' + self.track_id.display_name
                    return name




    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: r.company_id == line.order_id.company_id)
            #raise ValidationError(taxes)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes

    def _prepare_invoice_line(self):

        self.ensure_one()
        return {
        'display_type': self.display_type,
        'sequence': self.sequence,
        'name': self.name,
        'product_id': self.product_id.id,
        'product_uom_id': self.product_uom.id,
        'quantity': self.qty_to_invoice,
        'discount': self.discount,
        'price_unit': self.price_unit,
        'tax_ids': [(6, 0, self.tax_id.ids)],
        'analytic_account_id': self.order_id.analytic_account_id.id,
        'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        'sale_line_ids': [(4, self.id)],
        'company_id': self.company_id.id,
        'term_id': self.term_id.id,
        }

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        return True

    @api.model
    def create(self, vals):
        record = super(SaleOrderLine, self).create(vals)
        record['company_id'] = self.env['sale.order'].browse(vals['order_id']).company_id.id
        if record.event_ticket_id:
            record['course_id'] = record.event_ticket_id.event_id.course_id.id
        
        return record

    def write(self, vals):
        event_ticket_id = self.event_ticket_id
        if 'event_ticket_id' in vals:
            event_ticket_id = self.env['event.event.ticket'].browse(vals['event_ticket_id'])

        if event_ticket_id:
            vals['course_id'] = event_ticket_id.event_id.course_id.id

        res = super(SaleOrderLine, self).write(vals)


    def _get_display_price(self, product):
        if self.event_ticket_id and self.event_id:
            currency = self.event_ticket_id.company_currency
            price = currency._convert(
                self.event_ticket_id.price, self.order_id.pricelist_id.currency_id,
                self.order_id.company_id,
                self.order_id.date_order or fields.Date.today())
            #if self.order_id.pricelist_id.currency_id == self.event_ticket_id.company_currency:
            #rate = self.order_id.pricelist_id.currency_id._get_conversion_rate(self.env.ref('base.USD'),self.order_id.pricelist_id.currency_id, self.order_id.company_id, self.order_id.date_order or fields.Date.today())
            #price = price / rate
            return price

        else:
            return super()._get_display_price(product)


    @api.model
    def update_data(self, vals):
        return self.with_user(SUPERUSER_ID).write(vals)

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        vals = {} 
        company_price = self.env['company.price'].sudo().search([('company_id','=',self.company_id.id),
            ('product_tmpl_region_id','=',self.product_id.product_tmpl_id.id)],limit=1)
        
        if company_price:
            if company_price.override_default_price > 0:
                if self.order_id.currency_id.name != 'USD':
                    vals['price_unit'] = self.env.ref('base.USD')._convert(company_price.override_default_price,company_price.company_currency,self.order_id.company_id,self.order_id.date_order)

                else:
                    vals['price_unit'] = company_price.override_default_price

            else:
                if self.order_id.currency_id.name != 'USD':
                    vals['price_unit'] = self.env.ref('base.USD')._convert(company_price.price,company_price.company_currency,self.order_id.company_id,self.order_id.date_order)

                else:
                    vals['price_unit'] = company_price.price
            
        self.update(vals)

        return res


