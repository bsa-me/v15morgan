from odoo import models, fields


class Registration(models.Model):
    _inherit = 'event.registration'
    mrm_id = fields.Integer('MRM ID')
    from_mrm = fields.Boolean()
