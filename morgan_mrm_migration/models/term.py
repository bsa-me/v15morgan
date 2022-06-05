from odoo import models, fields


class Term(models.Model):
    _inherit = 'term'
    mrm_id = fields.Integer('MRM ID')
