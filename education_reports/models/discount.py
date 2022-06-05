from odoo import api, fields, models
from datetime import datetime


class Discount(models.Model):
    _name = 'sale.order.discount'
    discount_percentage = fields.Float('Discount Percentage',required=True)
    _sql_constraints = [
        ('discount_uniq', 'unique (discount_percentage)', "This Discount already exists !"),
        ]
    
    def name_get(self):
        result = []
        for record in self:
            name = str(record.discount_percentage) + '%'
            result.append((record.id, name))
        return result


