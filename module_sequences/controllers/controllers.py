# -*- coding: utf-8 -*-
from openerp import http

# class ModuleSequences(http.Controller):
#     @http.route('/module_sequences/module_sequences/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/module_sequences/module_sequences/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('module_sequences.listing', {
#             'root': '/module_sequences/module_sequences',
#             'objects': http.request.env['module_sequences.module_sequences'].search([]),
#         })

#     @http.route('/module_sequences/module_sequences/objects/<model("module_sequences.module_sequences"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('module_sequences.object', {
#             'object': obj
#         })