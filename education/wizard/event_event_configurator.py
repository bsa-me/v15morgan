# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields
import time


class EventConfigurator(models.TransientModel):
    _inherit = 'event.event.configurator'
    company_id = fields.Many2one('res.company',string='Company',readonly=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            val = {}
            val['domain'] = {'event_id': ['|',('is_global','=',True),('company_id','=',self.company_id.id),('event_ticket_ids.product_id','=', self.product_id.id),('date_end','>=',time.strftime('%Y-%m-%d 00:00:00'))]}
            return val

    @api.onchange('event_id')
    def onchange_event_id(self):
        if self.event_id:
            order = self.env['sale.order'].browse(self.env.context.get('active_id'))