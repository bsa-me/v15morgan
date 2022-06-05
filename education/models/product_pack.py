

from odoo import models, fields


class ProductPack(models.Model):
	_inherit = 'product.pack'
	course_id = fields.Many2one('course','Course')