from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class Expenses(models.Model):
    _inherit = "hr.expense"
    event_id = fields.Many2one('event.event','Event')
    term_id = fields.Many2one('term',string='Term')
    campaign_id = fields.Many2one('utm.campaign',string='Campaign')
    medium_id = fields.Many2one('utm.medium',string='Medium')
    source_id = fields.Many2one('utm.source',string='Source')
    is_campaign = fields.Boolean()
    program_id = fields.Many2one('program','Program')


    @api.onchange('product_id')
    def onchange_product(self):
    	if self.is_campaign:
    		if self.product_id:
    			date = datetime.now().strftime('%Y-%m-%d')
    			self.unit_amount = self.env.ref('base.USD')._convert(self.product_id.lst_price,self.currency_id,self.company_id,date)
    		else:
    			self.unit_amount = 0

    @api.onchange('currency_id')
    def onchange_currency(self):
    	if self.is_campaign:
    		if self.product_id and self.currency_id:
    			date = datetime.now().strftime('%Y-%m-%d')
    			self.unit_amount = self.env.ref('base.USD')._convert(self.product_id.lst_price,self.currency_id,self.company_id,date)
    		else:
    			self.unit_amount = 0


