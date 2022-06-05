# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import Controller, request, route

class Referral(Controller):

	@route(['/odoo_check_all_companies/go'], type='json', auth='user', method='POST', website=True)
	def referral_go(self):
		return {'link': request.env.user.get_allowed_companies_url()}