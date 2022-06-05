
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    resume_id = fields.Many2one('res.partner')
    obtained_via = fields.Selection([('morgan', 'Morgan'),('competitor', 'Competitor'),('supplier', 'Directly with Supplier')],string='Obtained Via')
    study_format = fields.Selection([('liveclass', 'Live Class'),('liveonline', 'Live Online'),('self', 'Self Study')],string='Study Format')
    language = fields.Many2one('res.lang','Language')
    lang_type = fields.Selection([('basic', 'Basic'),('intermediate', 'Intermediate'),('profficient', 'Profficient')],string='Language Type')
    program_id = fields.Many2one('program','Program')
    course_ids = fields.Many2many('course',string='Courses')
    topic_ids = fields.Many2many('course.topic',string='Topics', domain="[('course_id','in',course_ids)]")
    education = fields.Selection([('phd', 'PHD'),('ms', 'MS'),('mba', 'MBA'),('ba','BA'),('BS','BS'),('0','0'),('other','Other')],string='Education')
    major_id = fields.Many2one('instructor.major','Major')
    unversity_id = fields.Many2one('university','University')
    company = fields.Char(string='Company')
    job_title = fields.Char(string='Job Title')
    years_of_experience = fields.Char('Years of experience')
    skill_type = fields.Selection(related='line_type_id.skill_type',string='SKill Type')
    date_start = fields.Date(required=False)
    cpe_validity_date = fields.Date('CPE Validity Date')

    @api.onchange('date_start','date_end')
    def onchange_date(self):
        if self.line_type_id.skill_type == 'experience':
            date_end = datetime.now().date()
            if self.date_start:
                if self.date_end:
                    date_end = self.date_end
                difference = relativedelta(date_end, self.date_start)
                self.years_of_experience = str(difference.years)

