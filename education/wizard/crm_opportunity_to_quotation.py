# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Opportunity2Quotation(models.TransientModel):

    _inherit = 'crm.quotation.partner'

    event_id = fields.Many2one('event.event','Event')
    event_ticket_id = fields.Many2one('event.event.ticket')

    @api.model
    def default_get(self, fields):
        result = super(Opportunity2Quotation, self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model != 'crm.lead':
            raise UserError(_('You can only apply this action from a lead.'))

        active_id = self._context.get('active_id')
        if 'lead_id' in fields and active_id:
            result['lead_id'] = active_id
            lead = self.env['crm.lead'].browse(active_id)
            if lead.event_id:
                result['event_id'] = lead.event_id.id

        return result

    def action_apply(self):
        self.ensure_one()
        if self.action != 'nothing':
            self.lead_id.write({
                'partner_id': self.partner_id.id if self.action == 'exist' else self._create_partner(),
                'event_ticket_id': self.event_ticket_id.id if self.event_ticket_id else False
            })
            self.lead_id._onchange_partner_id()

        return self.lead_id.action_new_quotation()

