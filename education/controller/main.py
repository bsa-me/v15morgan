# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging
_logger = logging.getLogger(__name__)


class EventTicket(http.Controller):

	@http.route('/update_line', type='json', auth="public", methods=['POST'], website=True)
	def update_line(self, **kw):
		vals = {}

		if kw.get('line_id'):
			order_line = request.env['sale.order.line'].sudo().browse(kw.get('line_id'))

		if kw.get('event_id'):
			vals['event_id'] = kw.get('event_id')
			vals['name'] = request.env['event.event'].browse(kw.get('event_id')).display_name

		if kw.get('event_ticket_id'):
			vals['event_ticket_id'] = kw.get('event_ticket_id')

		if kw.get('price_unit'):
			vals['price_unit'] = kw.get('price_unit')

		print('Order line vals are ' + str(vals))
		if order_line:
			order_line.update_data(vals)
