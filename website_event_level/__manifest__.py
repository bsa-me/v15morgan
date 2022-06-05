# -*- coding: utf-8 -*-
{
    'name': "Events Level",

    'summary': """Filter events by level on website""",

    'description': """
        Publish Courses
    """,

    'author': "Al Jawad software house",
    'website': "https://www.al-jawad.ae",
    'company': "Al Jawad software house",

    'category': 'Website',
    'version': '0.1',

    'depends': ['education'],

    'data': [
        'security/ir.model.access.csv',
        'views/event_templates.xml',
        'views/event_views.xml',
        'views/course_views.xml',
        'views/payment_template.xml',
        'views/sale_order.xml',
        'views/website_menu.xml',
        #'views/assets.xml',
    ],
}
