# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class SaleReport(models.Model):
	_inherit='sale.report'

	event_id = fields.Many2one('event.event','Event',readonly=True)
	product_categ_id = fields.Many2one('product.category','Product Category',readonly=True)
	term_id = fields.Many2one('term','Term', readonly=True)
	study_format = fields.Many2one('event.type','Study Format', readonly=True)

	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
		fields['event_id'] = ', l.event_id as event_id'
		fields['product_categ_id'] = ', l.product_categ_id as product_categ_id'
		fields['term_id'] = ', l.term_id as term_id'
		fields['study_format'] = ', l.study_format as study_format'

		groupby += ', l.event_id, l.product_categ_id, l.term_id, l.study_format'
		return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)