from odoo import models, fields


class Term(models.Model):
    _inherit = 'attendance'
    mrm_id = fields.Integer('MRM ID')
