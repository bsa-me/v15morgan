from odoo import models, fields


class EducationLevel(models.Model):
    _name = 'education.level'
    name = fields.Char('Name')
    old_id = fields.Integer()
    