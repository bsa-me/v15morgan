# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):

    _inherit = 'crm.lead2opportunity.partner'
    

    def _create_partner(self, lead_id, action, partner_id):
        if action == 'each_exist_or_create':
            partner_id = self.with_context(active_id=lead_id)._find_matching_partner()
            action = 'create'


        result = self.env['crm.lead'].browse(lead_id).handle_partner_assignation(action, partner_id)
        partner = self.env['res.partner'].browse(result[lead_id])
        lead = self.env['crm.lead'].browse(lead_id)
        partner.write({'first_name': lead.first_name, 'last_name': lead.last_name, 'middle_name': lead.middle_name, 'account_type': 'b2c','industry_id': lead.industry_id.id if lead.industry_id else False})
        return result.get(lead_id)
    
    @api.onchange('user_id')
    def _onchange_user(self):
        return False