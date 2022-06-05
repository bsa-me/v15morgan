

from odoo import models, fields


class ProductCategory(models.Model):
	_inherit = 'product.category'
	mrm_id = fields.Integer()