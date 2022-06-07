# -*- coding: utf-8 -*-
{
    'name': "accounting_workflow",

    'summary': """
        Accounting Workflow""",

    'description': """
        
    """,

    'author': "Business Solution Advisors",
    'website': "http://www.bsa-me.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_accountant', 'sale'],

    # always loaded
    'data': [
        'data/automated_actions.xml',
        'data/mail_template.xml',
        'data/cron.xml',
        'views/sale_order.xml',
    ],
}
