# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sh_street = fields.Char()
    sh_street2 = fields.Char()
    sh_zip = fields.Char(change_default=True)
    sh_city = fields.Char()
    sh_state_id = fields.Char()
    sh_country_id = fields.Char()
    additional_no = fields.Char("Additional No", translate=True)
    other_seller_id = fields.Char("Other Seller Id", translate=True)
    district = fields.Char(translate=True)

    # make some fields translatable
    first_name = fields.Char('First Name', translate=True)
    middle_name = fields.Char('Middle Name', translate=True)
    last_name = fields.Char('Last Name', translate=True)
    street = fields.Char(translate=True)
    zip = fields.Char(change_default=True, translate=True)
    organisme_collecteur = fields.Char('Organisme Collecteur', translate=True)
    fax = fields.Char('Fax', translate=True)
    postal_code = fields.Char('Postal Code', translate=True)
    university = fields.Char('University', translate=True)
    phone = fields.Char('Phone', translate=True)
    mobile = fields.Char('Mobile', translate=True)
    function = fields.Char(string='Job Position', translate=True)
    vat = fields.Char('Tax Registration Number', translate=True)
    arabic_vat = fields.Char()
    number_departments = fields.Char('Num Departments', translate=True)
    number_employees = fields.Char('Num Employees', translate=True)
