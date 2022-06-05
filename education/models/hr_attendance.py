from odoo import models, fields
from datetime import datetime


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    session_id = fields.Many2one('event.track')
    same_date = fields.Boolean(compute="_compute_same_date")
    session_date = fields.Datetime(related="session_id.date",string='Session Date')
    session_course = fields.Many2one('course',related="session_id.course_id",string='Course')
    track_from = fields.Float(related="session_id.track_from",string="From")
    to = fields.Float(related="session_id.to",string="To")
    duration = fields.Float(related="session_id.duration",string="Duration")
    contract_currency_id = fields.Many2one('res.currency',string="Currency",compute="_compute_amount")
    gross_rate = fields.Monetary(compute="_compute_amount",string="Gross Rate", currency_field='contract_currency_id')

    def _compute_same_date(self):
    	for record in self:
    		check_in = False
    		check_out = False
    		session_date = False
    		record['same_date'] = False

    		if record.check_in:
    			check_in = record.check_in.date()

    		if record.check_out:
    			check_out = record.check_out.date()

    		if record.session_date:
    			session_date = record.session_date.date()

    		if session_date:
    			if check_out:
    				if session_date != check_in or session_date != check_out:
    					record['same_date'] = True

    			else:
    				if session_date != check_in or session_date:
    					record['same_date'] = True


    def _compute_amount(self):
        for record in self:
            record['contract_currency_id'] = False
            record['gross_rate'] = 0
            contract = self.env['hr.contract'].search([('company_id','=',record.employee_id.company_id.id),('course_ids','in',record.session_course.id),('state','=','open')],limit=1)
            if contract:
                record['contract_currency_id'] = contract.currency_id.id
                record['gross_rate'] = record.worked_hours * contract.hourly_wage




