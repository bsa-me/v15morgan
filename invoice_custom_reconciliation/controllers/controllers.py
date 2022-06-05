# -*- coding: utf-8 -*-
# from odoo import http


# class InvoiceCustomReconciliation(http.Controller):
#     @http.route('/invoice_custom_reconciliation/invoice_custom_reconciliation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_custom_reconciliation/invoice_custom_reconciliation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_custom_reconciliation.listing', {
#             'root': '/invoice_custom_reconciliation/invoice_custom_reconciliation',
#             'objects': http.request.env['invoice_custom_reconciliation.invoice_custom_reconciliation'].search([]),
#         })

#     @http.route('/invoice_custom_reconciliation/invoice_custom_reconciliation/objects/<model("invoice_custom_reconciliation.invoice_custom_reconciliation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_custom_reconciliation.object', {
#             'object': obj
#         })
