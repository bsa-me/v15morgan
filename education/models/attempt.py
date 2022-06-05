from odoo import models, fields,api
from odoo.exceptions import UserError


class Attempt(models.Model):
    _name = 'attempt'
    _description = 'Attempt'

    name = fields.Char('Attempt',compute='_compute_attempt_number')
    type = fields.Selection(
        [
        ('attempt', 'Attempt'),
        ('examhomework', 'Exam & homework')
        ],
        string='Type')
    student_id = fields.Many2one('res.partner', string="Student")
    course_id = fields.Many2one('course', string="Course")
    event_id = fields.Many2one('event.event', string="Event",domain="[('course_id','=',course_id)]")
    topic_id = fields.Many2one('course.topic', string="Topic",domain="[('course_id','=',course_id)]")
    attempt_date = fields.Date('Attempt Date')
    passing_status = fields.Selection(
    	[
    	('passed', 'Passed'),
    	('failed', 'Failed')
    	],
    	string='Passing Status')
    score = fields.Float('Score')
    registration_id = fields.Many2one('event.registration')
    product_registration_id = fields.Many2one('product.registration')

    order_id = fields.Many2one('sale.order','Order')
    sale_order_line = fields.Many2one('sale.order.line','Sale order line')
    is_self_study = fields.Boolean(string='Is self study')
    expected_exam_date = fields.Date('Expected Exam Date')
    expected_result_date = fields.Date('Expected Result Date')
    expected_submittal_date = fields.Date('Expected Submittal Date')
    window_date_begin = fields.Datetime('Window Date')
    window_date_end = fields.Datetime('Window Date End')
    attempt_type = fields.Selection(
        [
        ('assignment', 'Assignment'),
        ('exam', 'Exam')
        ],
        string='Attempt Type')

    earned_credits = fields.Char('Credits Earned')



    
    def _compute_attempt_number(self):
       for record in self:
        attempts = self.search([('registration_id','=',record.registration_id.id),('id','<',record.id)])
       	count = len(attempts) + 1 if len(attempts) > 0 else 1
       	record['name'] = str(++count)

    @api.model
    def create(self, vals):
        record = super(Attempt, self).create(vals)
        if self.sale_order_line:
            if self.sale_order_line.event_id:
                record['event_id'] = self.sale_order_line.event_id.id

            else:
                record['is_self_study'] = True

        return record


    @api.constrains('attempt_date')
    def _check_attempt_date(self):
        if self.attempt_date:
            if self.attempt_date > fields.Date.today():
                raise UserError("Attempt date cannot be greater than today's date")


    @api.onchange('registration_id')
    def onchange_reg(self):
        if self.registration_id.event_id:
            self.event_id = self.registration_id.event_id.id
            self.course_id = self.registration_id.event_id.course_id.id
