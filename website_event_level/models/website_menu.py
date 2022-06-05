# -*- coding: utf-8 -*-

from odoo import fields, models,api
from odoo.exceptions import UserError


class WebsiteMenu(models.Model):
	_inherit = 'website.menu'
	country_group_ids = fields.Many2many('res.country.group', 'website_menu_country_group_rel', 'website_menu_id', 'country_group_id',
											string='Country Groups')
