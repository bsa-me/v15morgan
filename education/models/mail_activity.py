from odoo import models, fields


class MailActivity(models.Model):
    _inherit = 'mail.activity'
    mrm_id = fields.Integer('MRM ID')