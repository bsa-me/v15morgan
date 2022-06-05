# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Odoo check all allowed companies",
    'summary': """Allow you to check all the allowed companies as logged in companies""",
    'category': 'Hidden',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        #'views/templates.xml',
        'wizard/select_companies.xml',
    ],
    'qweb': [
        #"static/src/xml/companies.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_check_all_companies/static/src/js/companies.js',
        ],
        'web.assets_qweb': [
            'odoo_check_all_companies/static/src/xml/companies.xml',
        ],
    },
    'auto_install': False,
}