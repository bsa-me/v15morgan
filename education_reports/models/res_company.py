from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    street = fields.Char(compute='_compute_address', inverse='_inverse_street', translate=False, store=False)
    street2 = fields.Char(compute='_compute_address', inverse='_inverse_street2', translate=False, store=False)
    city = fields.Char(compute='_compute_address', inverse='_inverse_city', translate=False, store=False)


class CountryState(models.Model):
    _inherit = 'res.country.state'

    name = fields.Char(string='State Name', required=True,
                       help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton',
                       translate=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    street = fields.Char(translate=True)
    street2 = fields.Char(translate=True)
    city = fields.Char(translate=True)
