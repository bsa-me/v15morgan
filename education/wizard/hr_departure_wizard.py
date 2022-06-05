# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class DepartureWizard(models.TransientModel):
	_inherit = 'hr.departure.wizard'
	departure_reason = fields.Selection([('fired', 'Suspended'),('resigned', 'Resigned'),('retired', 'Retired')], string="Departure Reason", default="fired")