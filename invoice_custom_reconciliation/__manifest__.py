# -*- coding: utf-8 -*-
{
    'name': "Invoice Reconciliation",

    'summary': """
    Invoice Reconciliation""",

    'description': """
        Invoice Reconciliation
    """,

    'author': "BSA",
    'website': "http://www.bsa-me.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','bi_customer_overdue_statement','education'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/account_payment_report.xml',
        'views/report_future_payment.xml',
        'wizard/register_payment.xml',
        'data/menu_items.xml',
        'data/mail_template_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
