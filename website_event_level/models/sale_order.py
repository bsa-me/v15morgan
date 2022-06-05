# -*- coding: utf-8 -*-

from odoo import fields, models


class Course(models.Model):
	_inherit = 'sale.order'
	exam_id = fields.Many2one('exam',string='Exam Window') 