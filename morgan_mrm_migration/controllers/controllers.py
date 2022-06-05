# -*- coding: utf-8 -*-
# from odoo import http


# class MorganMrmMigration(http.Controller):
#     @http.route('/morgan_mrm_migration/morgan_mrm_migration/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/morgan_mrm_migration/morgan_mrm_migration/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('morgan_mrm_migration.listing', {
#             'root': '/morgan_mrm_migration/morgan_mrm_migration',
#             'objects': http.request.env['morgan_mrm_migration.morgan_mrm_migration'].search([]),
#         })

#     @http.route('/morgan_mrm_migration/morgan_mrm_migration/objects/<model("morgan_mrm_migration.morgan_mrm_migration"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('morgan_mrm_migration.object', {
#             'object': obj
#         })
