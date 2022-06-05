
from odoo import models, fields, api


class CertificationStatus(models.Model):
    _name = 'certification.status'
    name = fields.Char()