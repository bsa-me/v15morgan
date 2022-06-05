import json
import requests
import xmlrpc.client as xmlrpclib
import base64
from datetime import timedelta,datetime
from odoo import models, fields


class Pgoram(models.Model):
    _inherit = 'program'
    mrm_id = fields.Integer('MRM ID')
    active = fields.Boolean(default=True)