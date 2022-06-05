# -*- coding: utf-8 -*-
from odoo import models, fields, api



class SaleOrder(models.Model):
	_inherit = 'sale.order'
	
	partner_id = fields.Many2one('res.partner', string='Customer', readonly=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, default='_default_partner', track_visibility='always')

	def _default_partner(self):
		if(self.opportunity_id):
			return self.opportunity_id.partner_id.id
		return False


		

		



