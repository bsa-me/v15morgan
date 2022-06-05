from odoo import models, fields, api, _
import datetime
from odoo.exceptions import ValidationError

class UtmSource(models.Model):
	_inherit = "utm.source"
	expense_ids = fields.One2many('hr.expense','source_id',string='Expenses')
	company_id = fields.Many2one(string="Region", domain="[('is_region', '=', True)]",default=lambda self: self._get_child_companies())
	
	def _get_child_companies(self):
		company = self.env.company
		child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
		if child_company:
			return child_company.id
		else:
			return company.id