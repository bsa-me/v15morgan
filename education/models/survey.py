from odoo import models, fields, api


class Survey(models.Model):
    _inherit = "survey.survey"
    survey_type = fields.Selection(
        [
        ('marketing', 'Marketing'),
        ('instructor', 'Instructor Review'),
        ('exam', 'Exam'),
        ('event', 'Event Review'),
        ('end', 'End Of Event Review')
        ],
        string='Survey Type')
    instructor_id = fields.Many2one(
        'hr.employee',
        string="Instructor",
        domain="[('is_instructor', '=', True)]"
        )
    event_id = fields.Many2one('event.event', string="Event")
    session_id = fields.Many2one('event.track', string="Session",domain="[('event_id','=',event_id)]")
    survey_id = fields.Many2one('res.partner')
    title = fields.Char('Title')
    survey_id = fields.Many2one('event.event')

    @api.onchange('event_id')
    def onchange_event_id(self):
        if self.event_id:
            val = {}
            val['domain'] = {'instructor_id': [('id', 'in', self.event_id.organizer_ids.ids)]}
            return val

    @api.onchange('session_id')
    def onchange_session(self):
        if self.session_id:
            if self.session_id.employee_id:
                self.instructor_id = self.session_id.employee_id.id

            else:
                self.instructor_id = False

        else:
            self.instructor_id = False



