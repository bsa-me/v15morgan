from odoo import fields, models

class Slide(models.Model):
	_inherit = "slide.channel"
	nbr_iframe = fields.Integer("Number of iframes", compute="_compute_slides_statistics", store=True)

