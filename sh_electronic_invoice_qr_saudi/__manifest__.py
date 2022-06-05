# -*- coding: utf-8 -*-
{
    "name": "Electronic invoice KSA - Sale, Purchase, Invoice, Credit Note, Debit Note | Saudi Invoice QR Code  | Invoice based on TLV Base64 string QR Code | Saudi Electronic Invoice with Base64 TLV QRCode",
    'author': "Al Jawad software house",
    'website': "https://www.al-jawad.ae",
    "support": "support@aljawad-ae",
    'version': '13.0.1',
    'category': "Accounting",
    'summary': "Electronic invoice KSA Sale Saudi Electronic Invoice for Purchase Receipt Saudi VAT E-Invoice for Account QR Saudi VAT E-Invoice for POS Electronic Invoice with QR code arabic translations ZATCA QR Code Saudi VAT Invoice Saudi E-Invoice Odoo",
    'description': """This module allows you to print a Saudi electronic invoice with a QR code in the sale, purchase, invoice, credit note With Base64 TLV QR Code. You can display the data of VAT with tax details in the sale, purchase, invoice, credit note With Base64 TLV QR Code. You can print receipts in regional and global languages, such as Arabic and English As per Saudi Arabia Zakat's regulations to apply specific terms to the electronic invoice by 4th of Dec 2021.""",
    "depends" : ["account","base","sale_management","purchase"],
    "application" : True,
    "data" : [  
            'security/ir.model.access.csv',
            'report/sale_report_templates.xml',
            'report/sale_report.xml',
            'report/report_invoice.xml',
            'views/account_report.xml',
            'security/qr_elements_security.xml',
            'views/res_company.xml',
            'views/res_partner.xml',
            'views/account_move.xml',
            'report/invoice_report.xml',
            'report/account_simplified_report.xml',
            'report/report_action.xml',
            'report/invoice_external_layout.xml',
            'views/sale_order.xml',
            'report/sale_order_report.xml',
            #'views/purchase_order.xml',
            #'report/purchase_order_report.xml',
            'views/inherit_product.xml'
            ],
    
    "external_dependencies": {
        "python": ["qrcode"],
    },
    "auto_install":False,
    "installable" : True,
}
