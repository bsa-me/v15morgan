# -*- coding: utf-8 -*-

from odoo import fields, models,api
from odoo.exceptions import UserError


class Event(models.Model):
	_inherit = 'event.event'
	level_id = fields.Many2one('event.level')
	country_group_ids = fields.Many2many('res.country.group', 'event_country_group_rel', 'event_id', 'country_group_id',
											string='Country Groups')

	@api.model
	def _search_get_detail(self, website, order, options):
		res = super()._search_get_detail(website, order, options)
		domain = res['base_domain']
		domain.append([('country_group_ids','!=',False)])
		level = options.get('level', 'all')
		if level != 'all':
			domain.append([("level_id", "=", int(level))])
		program = options.get('program', 'all')
		if program != 'all':
			domain.append([("program_id", "=", int(program))])
		company = options.get('company', 'all')
		if company != 'all':
			domain.append([("company_id", "=", int(company))])
		event_period = options.get('event_period', 'all')
		if event_period != 'all':
			domain.append([("period_id", "=", int(event_period))])
		res['base_domain'] = domain
		#raise UserError(str(res))
		return res


	@api.onchange('course_id')
	def onchange_course_level(self):
		if self.course_id:
			if self.course_id.level_id:
				self.level_id = self.course_id.level_id.id

			else:
				self.level_id = False

		else:
			self.level_id = False

class Event(models.Model):
	_inherit = 'event.event.ticket'
	country_group_ids = fields.Many2many('res.country.group', 'event_ticket_country_group_rel', 'event_ticket_id', 'country_group_id',string='Country Groups')