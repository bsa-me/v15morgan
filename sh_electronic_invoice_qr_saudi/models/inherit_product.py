# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import api,models, fields


class Productinherit(models.Model):
    _inherit = 'product.product'

    sh_arabic_name = fields.Char(string='Custom Name')


class ProductTemplateinherit(models.Model):
    _inherit = 'product.template'

    sh_arabic_name = fields.Char(string='Custom Name', related='product_variant_ids.sh_arabic_name', readonly=False)

    @api.model
    def create(self, vals):
        res = super(ProductTemplateinherit, self).create(vals)
        if vals.get("sh_arabic_name", False):
            tags = vals.get("sh_arabic_name")
            if res and res.product_variant_id:
                res.product_variant_id.sh_arabic_name = tags

        return res