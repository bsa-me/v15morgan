# -*- coding: utf-8 -*-
{
    'name': "Training Reports",

    'summary': """
        """,

    'description': """
        
    """,

    'author': "Business Solution Advisors",
    'website': "http://www.bsa-me.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['event', 'education'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/event_event.xml',
        'views/event_registration.xml',
        'views/event_track.xml',
        'views/purchase_order.xml',
        'views/utm_campaing.xml',
        'views/sale_order.xml',
    ],
}
