# -*- coding: utf-8 -*-
{
    'name': "Mass mailing dynamic placeholder generator",

    'summary': """
    Mass mailing dynamic placeholder generator""",

    'description': """
        This module allows you to generate a dynamic placeholder for mass mailing.
    """,

    'author': "BSA",
    'website': "http://www.bsa-me.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Email Marketing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mass_mailing'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/mailing_mailing.xml',
    ],
}
