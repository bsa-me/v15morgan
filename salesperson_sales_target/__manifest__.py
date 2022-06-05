# -*- coding: utf-8 -*-
{
    'name': "Sales Target for Salesperson",

    'summary': """
    Sales Target for Salesperson""",

    'description': """
        This module allows to assign and track sales target to salesperson.
    """,

    'author': "BSA",
    'website': "http://www.bsa-me.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','education'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
