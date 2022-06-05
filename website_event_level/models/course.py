# -*- coding: utf-8 -*-

from odoo import fields, models


class Course(models.Model):
	_inherit = 'course'

	level_id = fields.Many2one('event.level')