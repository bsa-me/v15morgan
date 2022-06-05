from odoo import api, fields, models


class Sign(models.Model):
    _inherit = 'sign.template'

    fields_of = fields.Selection([('partner', 'Partner'), ('registration', 'Registration')], string='Fields of')
    event_reg_id = fields.Many2one('event.registration')
    
