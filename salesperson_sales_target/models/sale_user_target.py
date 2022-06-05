from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SalesTarget(models.Model):
    _name = 'sale.user.target'
    _description = 'Sales target for salesperson'
    user_id = fields.Many2one('res.users',string='Salesperson', required=1)
    date_from = fields.Date(string='Date From', required=1)
    date_to = fields.Date(string='Date To', required=1)
    target = fields.Float('Target')
    actual_sales = fields.Float('Actual Sales', compute="_compute_actual_sales")
    actual_vs_target = fields.Float('Actucal vs Target(%)', compute="_compute_actual_vs_target")
    company_id = fields.Many2one('res.company',string='Region',domain="[('is_region', '=', True)]",default=lambda self: self._get_child_companies(), required=1)
    currency_id = fields.Many2one(related='company_id.currency_id',string='Currency',store=True)
    term_id = fields.Many2one('term','Targeted Term')
    program_id = fields.Many2one('program','Program')
    event_id = fields.Many2one('event.event','Event',domain="['|',('is_global','=',True),('company_id','=',company_id),('term_id','=',term_id),('program_id','=',program_id),('state','=','confirm')]")
    study_format = fields.Selection([('multiple','Multiple Formats'),('live','Live Class'),('liveonline','Live Online'),('self','Self-Study'),('online','Online'),('inhouse','In House'),('private','Private Tutoring'),('other','Other'),('standalone','StandAlone'),('workshop','Workshop')],string='Study Format')


    def _get_child_companies(self):
    	company = self.env.company
    	child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
    	if child_company:
    		return child_company.id
    	else:
    		return company.id


    @api.constrains('target')
    def _check_target_sign(self):
    	if self.target < 0:
    		raise ValidationError('Target shoud be positive')

    def _compute_actual_sales(self):
    	for record in self:
    		date = fields.Date.today()
    		total_amount = 0
    		currency = record.currency_id
    		order_lines = self.env['sale.order.line'].search([('order_id.state','in',['sale','done']),('order_id.date_order','>=',record.date_from),('order_id.date_order','<=',record.date_to),('order_id.user_id','=',record.user_id.id),('order_id.company_id','=',record.company_id.id),
                ('event_id','=',record.event_id.id),('term_id','=',record.term_id.id)])
    		if order_lines:    			
    			for line in order_lines:
    				total_amount += currency._convert(line.price_subtotal, line.order_id.currency_id, line.order_id.company_id, date)

    		record['actual_sales'] = total_amount

    def _compute_actual_vs_target(self):
    	for record in self:
    		result = (record.actual_sales/record.target)*100
    		record['actual_vs_target'] = result




