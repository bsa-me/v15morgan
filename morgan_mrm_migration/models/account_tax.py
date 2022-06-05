import json
import requests
import xmlrpc.client as xmlrpclib
import base64
from datetime import timedelta,datetime
from odoo import models, fields
from odoo.exceptions import UserError


class Tax(models.Model):
    _inherit = 'account.tax'
    mrm_id = fields.Integer('MRM ID')