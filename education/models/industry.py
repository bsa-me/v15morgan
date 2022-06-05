from odoo import models, fields


class Indusry(models.Model):
    _name = 'industry'
    _description = 'Industry'
    name = fields.Char('Industry')

class Indusry(models.Model):
    _inherit = 'res.partner.industry'
    old_id = fields.Integer()
    
