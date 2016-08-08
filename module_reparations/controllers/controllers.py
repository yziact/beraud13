# -*- coding: utf-8 -*-
from openerp import http

# class Module-reparations(http.Controller):
#     @http.route('/module-reparations/module-reparations/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/module-reparations/module-reparations/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('module-reparations.listing', {
#             'root': '/module-reparations/module-reparations',
#             'objects': http.request.env['module-reparations.module-reparations'].search([]),
#         })

#     @http.route('/module-reparations/module-reparations/objects/<model("module-reparations.module-reparations"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('module-reparations.object', {
#             'object': obj
#         })

