# -*- coding: utf-8 -*-

import babel.dates
import re
import werkzeug
from werkzeug.datastructures import OrderedMultiDict

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.osv import expression

from odoo import fields, http, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.http import request
from odoo.tools.misc import get_lang
from odoo.exceptions import ValidationError

from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.website_sale.controllers.main import WebsiteSale

class CustomWebsiteEventController(WebsiteEventController):
	def sitemap_event(env, rule, qs):
		if not qs or qs.lower() in '/events':
			yield {'loc': '/events'}
	
	@http.route(['/event', '/event/page/<int:page>', '/events', '/events/page/<int:page>'], type='http', auth="public", website=True, sitemap=sitemap_event)
	def events(self, page=1, **searches):
		Event = request.env['event.event']
		SudoEventType = request.env['event.type'].sudo()
		searches.setdefault('search', '')
		searches.setdefault('date', 'all')
		searches.setdefault('tags', '')
		searches.setdefault('type', 'all')
		searches.setdefault('country', 'all')
		searches.setdefault('level', 'all')
		searches.setdefault('program', 'all')
		searches.setdefault('company', 'all')
		searches.setdefault('event_period', 'all')
		website = request.website

		step = 12  # Number of events per page

		options = {
			'displayDescription': False,
			'displayDetail': False,
			'displayExtraDetail': False,
			'displayExtraLink': False,
			'displayImage': False,
			'allowFuzzy': not searches.get('noFuzzy'),
			'date': searches.get('date'),
			'tags': searches.get('tags'),
			'type': searches.get('type'),
			'country': searches.get('country'),
			'level': searches.get('level'),
			'program': searches.get('program'),
			'company': searches.get('company'),
			'event_period': searches.get('event_period'),
		}
		order = 'date_begin'
		if searches.get('date', 'all') == 'old':
			order = 'date_begin desc'
		order = 'is_published desc, ' + order
		search = searches.get('search')
		event_count, details, fuzzy_search_term = website._search_with_fuzzy("events", search,
			limit=page * step, order=order, options=options)
		event_details = details[0]
		events = event_details.get('results', Event)
		#check country groups
		country = request.session.geoip.get('country_code') if request and request.session.geoip else False
		country_id = False
		if country:
			country_id = request.env['res.country'].search([('code', '=', country)], limit=1).id
			events = events.filtered(lambda e: country_id in e.country_group_ids.mapped('country_ids').ids)

		events = events[(page - 1) * step:page * step]
		# count by domains without self search
		domain_search = [('name', 'ilike', fuzzy_search_term or searches['search'])] if searches['search'] else []

		no_date_domain = event_details['no_date_domain']
		dates = event_details['dates']
		for date in dates:
			if date[0] != 'old':
				date[3] = Event.search_count(expression.AND(no_date_domain) + domain_search + date[2])

		no_country_domain = event_details['no_country_domain']
		countries = Event.read_group(expression.AND(no_country_domain) + domain_search, ["id", "country_id"],
			groupby="country_id", orderby="country_id")
		countries.insert(0, {
			'country_id_count': sum([int(country['country_id_count']) for country in countries]),
			'country_id': ("all", _("All Countries"))
		})


		level_domain = domain_search + [('id','in',events.ids),('level_id','!=',False)]
		levels = Event.read_group(level_domain, ["id", "level_id"],
			groupby="level_id", orderby="level_id")
		
		#raise ValidationError(levels)
		levels.insert(0, {
			'level_id_count': sum([int(level['level_id_count']) for level in levels]),
			'level_id': ("all", _("All Levels"))
		})

		program_domain = domain_search + [('id','in',events.ids),('program_id','!=',False)]
		programs = Event.read_group(program_domain, ["id", "program_id"],
			groupby="program_id", orderby="program_id")
		programs.insert(0, {
			'program_id_count': sum([int(program['program_id_count']) for program in programs]),
			'program_id': ("all", _("All Programs"))
		})

		company_domain = domain_search + [('id','in',events.ids),('company_id','!=',False)]
		companies = Event.read_group(company_domain, ["id", "company_id"],
			groupby="company_id", orderby="company_id")
		companies.insert(0, {
			'company_id_count': sum([int(company['company_id_count']) for company in companies]),
			'company_id': ("all", _("All Companies"))
		})

		period_domain = domain_search + [('id','in',events.ids),('period_id','!=',False)]
		periods = Event.read_group(period_domain, ["id", "period_id"],
			groupby="period_id", orderby="period_id")
		periods.insert(0, {
			'period_id_count': sum([int(period['period_id_count']) for period in periods]),
			'period_id': ("all", _("All Periods"))
		})

		search_tags = event_details['search_tags']
		current_date = event_details['current_date']
		current_type = None
		current_country = None
		current_level = None
		current_program = None
		current_company = None
		current_period = None

		if searches["type"] != 'all':
			current_type = SudoEventType.browse(int(searches['type']))

		if searches["country"] != 'all' and searches["country"] != 'online':
			current_country = request.env['res.country'].sudo().browse(int(searches['country']))

		if searches["level"] != 'all':
			current_level = request.env['event.level'].sudo().browse(int(searches['level']))

		if searches["program"] != 'all':
			current_program = request.env['program'].sudo().browse(int(searches['program']))

		if searches["company"] != 'all':
			current_company = request.env['res.company'].sudo().browse(int(searches['company']))

		if searches["event_period"] != 'all':
			current_period = request.env['event.period'].sudo().browse(int(searches['event_period']))

		pager = website.pager(
			url="/event",
			url_args=searches,
			total=event_count,
			page=page,
			step=step,
			scope=5)

		keep = QueryURL('/event', **{key: value for key, value in searches.items() if (key == 'search' or value != 'all')})

		searches['search'] = fuzzy_search_term or search

		values = {
			'current_date': current_date,
			'current_country': current_country,
			'current_level': current_level,
			'current_program': current_program,
			'current_company': current_company,
			'current_period': current_period,
			'current_type': current_type,
			'event_ids': events,  # event_ids used in website_event_track so we keep name as it is
			'dates': dates,
			'categories': request.env['event.tag.category'].search([('is_published', '=', True)]),
			'countries': countries,
			'levels': levels,
			'programs': programs,
			'companies': companies,
			'periods': periods,
			'pager': pager,
			'searches': searches,
			'search_tags': search_tags,
			'keep': keep,
			'search_count': event_count,
			'original_search': fuzzy_search_term and search,
		}

		if searches['date'] == 'old':
			# the only way to display this content is to set date=old so it must be canonical
			values['canonical_params'] = OrderedMultiDict([('date', 'old')])

		return request.render("website_event.index", values)


class WebsiteSale(WebsiteSale):
	@http.route(['/shop/exam_window'], type='json', auth="public", methods=['POST'], website=True)
	def customer_comment(self, **post):
		if post.get('exam_id'):
			order = request.website.sale_get_order()
			redirection = self.checkout_redirection(order)
			if redirection:
				return redirection

			if order and order.id:
				order.sudo().write({'exam_id': int(post.get('exam_id'))})

		return True






