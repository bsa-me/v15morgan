# -*- coding: utf-8 -*-
{
    'name': "Network AE Payment",
    'summary': """Payment Acquirer: Network AE""",
    'description': """Payment Acquirer: Network AE""",
    'author': "Al Jawad software house",
    'website': "https://www.al-jawad.ae",
    'category': 'Payment',
    'version': '0.1',
    'depends': ['payment', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/network_ae.xml',
        'views/payment_acquirer.xml',
        'views/sale_order.xml',
        'data/network_ae.xml',
    ],
    'application': True,
}
