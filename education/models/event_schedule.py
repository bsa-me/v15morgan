from odoo import models, fields,api


class EventSchedule(models.Model):
    _name = 'event.schedule'
    name = fields.Char(string='Name')
    schedule_id = fields.Many2one('event.event')
    day = fields.Selection(
    	[
    	('0', 'Monday'),
    	('1', 'Tuesday'),
    	('2', 'Wednesday'),
    	('3', 'Thursday'),
    	('4', 'Friday'),
    	('5', 'Saturday'),
    	('6', 'Sunday')],
    	        string='Day')
    event_id = fields.Many2one('event.event', string='Event')
    schedule_from = fields.Float(string='From')
    instructor_id = fields.Many2one('hr.employee', string='Instructor')
    schedule_to = fields.Float(string='To')
    course_id = fields.Many2one('course', string='Course', related='event_id.course_id', readonly=True)

    @api.onchange('event_id')
    def onchange_event_id(self):
        if self.event_id:
            val = {}
            val['domain'] = {'instructor_id': [('course_ids', 'in', [self.event_id.course_id.id])]}
            if not self.event_id.is_global:
                val['domain'] = {'instructor_id': [('contract_company_ids', 'in', [self.event_id.company_id.id]),('course_ids', 'in', [self.event_id.course_id.id])]}


            


            return val

