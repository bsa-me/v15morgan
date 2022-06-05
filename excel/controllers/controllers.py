# -*- coding: utf-8 -*-
from odoo import http

# class Excel(http.Controller):
#     @http.route('/excel/excel/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/excel/excel/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('excel.listing', {
#             'root': '/excel/excel',
#             'objects': http.request.env['excel.excel'].search([]),
#         })

#     @http.route('/excel/excel/objects/<model("excel.excel"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('excel.object', {
#             'object': obj
#         })