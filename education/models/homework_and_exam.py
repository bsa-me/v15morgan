from odoo import models, fields,api
from odoo.exceptions import UserError


class HomeWorkExam(models.Model):
    _name = 'homwork.and.exam'
    _description = 'Attempt'
    registration_id = fields.Many2one('event.registration','Registration')
    course_id = fields.Many2one('course')
    event_id = fields.Many2one('event.event',domain="[('course_id','=',course_id)]")
    topic_id = fields.Many2one('course.topic','Topic',domain="[('course_id','=',course_id)]")
    
