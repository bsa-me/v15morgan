# -*- coding: utf-8 -*-
{
    'name': "Export XML views as excel file",

    'summary': """
    Export views labels as excel file""",

    'description': """
        Export XML views as excel file
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','event_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/odoo_export.xml',
    ],
}
