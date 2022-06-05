from odoo import fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'
    currency_id = fields.Many2one('res.currency',related='contract_id.currency_id')
    worked_days_currency_id = fields.Many2one('res.currency',compute="_compute_currency")

    def _compute_currency(self):
    	for record in self:
    		record.worked_days_currency_id = False
    		for line in record.worked_days_line_ids:
    			if line.contract_currency_id:
    				record.worked_days_currency_id = line.contract_currency_id.id
    				break