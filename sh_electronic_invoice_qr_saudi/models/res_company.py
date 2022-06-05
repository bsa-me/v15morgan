# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import api, models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_name = fields.Char(string='Saudi Company Name', store=True, readonly=False)
    sh_street = fields.Char()
    sh_street2 = fields.Char()
    sh_zip = fields.Char()
    sh_city = fields.Char()
    sh_state_id = fields.Char()
    sh_country_id = fields.Char()
    additional_no = fields.Char("Additional No", translate=True)
    other_seller_id = fields.Char("Other Seller Id", translate=True)

    arabic_name = fields.Char(string='Company Arabic Name')
    arabic_address = fields.Text(string='Address in arabic',
                                 help='This address will printed in invoice header when the language is arabic')

    arabic_street = fields.Char()
    arabic_street2 = fields.Char()
    arabic_city = fields.Char()
    district = fields.Char()
    arabic_district = fields.Char()

    # make som fields translatable
    fax = fields.Char('Fax', translate=True)
    code = fields.Char('Code', required=True, translate=True)
    signature_name = fields.Char('Signer', translate=True)
    company_registry = fields.Char(translate=True)
