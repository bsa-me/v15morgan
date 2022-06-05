from odoo import models, fields, api
from datetime import datetime


class DecisionMaker(models.Model):
    _name = 'decision.maker'
    _description = 'Decision Maker'

    name = fields.Char('Name', required=1)
    