# -*- coding: utf-8 -*-

from odoo import fields, models


class Level(models.Model):
	_name = 'event.level'
	_description = 'Event Level'

	name = fields.Char('Level')
	
