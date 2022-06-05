from odoo import models, fields
from odoo.exceptions import UserError
import re


class InstructorEvaluation(models.Model):
    _name = 'mrm.instructor.evaluation'


    mrm_id = fields.Integer('MRM ID')
    course_id = fields.Many2one('course', 'Course',related=False,store=True)
    name = fields.Char('Title')
    session_id = fields.Many2one('event.track','Session')
    date = fields.Date('Date')
    average_score = fields.Float('Average Score')
    term_id = fields.Many2one('term', 'Term',related=False,store=True)
    instructor_id = fields.Many2one('hr.employee', 'Instructor',related=False,store=True)
    active_students = fields.Integer('Active Students')
    filled_evaluation = fields.Float('% Of class filled Evaluation')
    evaluation_form = fields.Html('Evaluation Form')
    region_id = fields.Many2one('res.company','Region',related=False,store=True)
    clean_evaluation_form = fields.Char(string='Clean Evaluation Form',compute="_compute_evaluation_form")
    type = fields.Selection([('public','Public'),('iht','IHT')],string='Evaluation Type',default='public')
    code = fields.Char('Code')
    partner_id = fields.Many2one('res.partner',string='Account')
    credentials = fields.Char('Credentials')
    topic_specialism = fields.Char('Topic Specialism')
    contract_notes = fields.Text('Contract Notes')



    def _compute_evaluation_form(self):
        for record in self:
            record['clean_evaluation_form'] = ''
            if record.evaluation_form:
                clean = re.compile('<.*?>')
                evaluation_form = re.sub(clean, '', record.evaluation_form)
                record['clean_evaluation_form'] = evaluation_form
    
