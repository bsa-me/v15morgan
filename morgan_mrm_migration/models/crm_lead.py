import json
import requests
import xmlrpc.client as xmlrpclib
import base64
from datetime import timedelta,datetime
from odoo import models, fields
from odoo.exceptions import UserError


class Lead(models.Model):
    _inherit = 'crm.lead'
    mrm_id = fields.Integer('MRM ID')
    mrm_user = fields.Char('MRM USER')
    migration_type = fields.Selection([('opportunity', 'Opportunity'),('submission', 'Submission'),('enquiry', 'Enquiry')],string='MRM type')
    mrm_age = fields.Integer('MRM age')
    mrm_create_date = fields.Date('MRM create date')
    mrm_invoice_total = fields.Float('MRM total invoiced')
    opportunity_mrm_id = fields.Integer('MRM Opportunity ID')
    mrm_subject = fields.Char('MRM Subject')
    mrm_body = fields.Text('MRM Body')
    mrm_dead_reason = fields.Text('MRM Dead Reason')
    mrm_url = fields.Char('MRM URL')
