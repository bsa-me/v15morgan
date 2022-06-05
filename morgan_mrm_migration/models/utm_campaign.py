from odoo import models, fields


class Campaign(models.Model):
    _inherit = 'utm.campaign'
    mrm_purpose = fields.Char('MRM Purpose')
    mrm_term_id = fields.Many2one('term','MRM TERM')
    mrm_cost = fields.Float('MRM Cost')
    mrm_start_date = fields.Date('MRM Start Date')
    mrm_end_date = fields.Date('MRM End Date')
