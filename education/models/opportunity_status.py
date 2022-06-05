from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class CrmStatus(models.Model):
    _name = 'crm.stage.status'
    name = fields.Char(required=True)
    stage_id = fields.Many2one('crm.stage',string='Opportunity Stage')
