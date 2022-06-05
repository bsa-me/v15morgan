# -*- coding: utf-8 -*-
{
    'name': "Blom Payment Acquirer",
    'summary': """Payment Acquirer: Blom""",
    'description': """Blom Payment Acquirer""",
    'author': "BSA",
    'website': "http://www.bsa-me.com",
    'category': 'Payment',
    'version': '0.1',
    'depends': ['payment','sale'],
    'data': [
        'views/blom.xml',
        'views/payment_acquirer.xml',
        'data/blom.xml',
        'views/payment_blom_template.xml',
        'views/sale_order.xml',
    ],
    'application': True,
}
