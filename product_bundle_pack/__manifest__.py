# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Product Bundle Pack",
    "category": 'Sales',
    "summary": """
       Combine two or more products together in order to create a bundle product.""",
    "description": """
	BrowseInfo developed a new odoo/OpenERP module apps.
	This module is use to create Product Bundle,Product Pack, Bundle Pack of Product, Combined Product pack.
    -Product Pack, Custom Combo Product, Bundle Product. Customized product, Group product.Custom product bundle. Custom Product Pack.
    -Pack Price, Bundle price, Bundle Discount, Bundle Offer.
	
    """,
    "sequence": 1,
    "author": "Browseinfo",
    "website": "http://www.browseinfo.in",
    "version": '11.0.0.2',
    "depends": ['sale','product','stock','sale_stock','sale_management'],
    "data": [
        'wizard/product_bundle_wizard_view.xml',
        'views/product_view.xml',
        'views/sale_order.xml',
        'security/ir.model.access.csv'
    ],
    "price": 25,
    "currency": 'EUR',
    "installable": True,
    "application": True,
    "auto_install": False,
    "images":['static/description/Banner.png'],

}
