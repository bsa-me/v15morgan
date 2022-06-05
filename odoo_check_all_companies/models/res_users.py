# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import uuid
import requests
import hmac
import threading

from hashlib import sha1
from werkzeug import url_encode

from odoo import api, models, tools


_logger = logging.getLogger(__name__)


class Users(models.Model):
    _inherit = 'res.users'

    def get_allowed_companies_url(self):

    	url_host = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

    	allowed_companies = self.env.user.company_ids.ids

    	companies = str(allowed_companies).replace('[',"")
    	companies = str(companies).replace(']',"")
    	companies = str(companies).replace(' ',"")

    	return url_host + '/web#cids=' + str(allowed_companies)