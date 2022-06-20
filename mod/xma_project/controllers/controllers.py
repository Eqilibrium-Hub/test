# -*- coding: utf-8 -*-
# from odoo import http


# class XmaProject(http.Controller):
#     @http.route('/xma_project/xma_project/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/xma_project/xma_project/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('xma_project.listing', {
#             'root': '/xma_project/xma_project',
#             'objects': http.request.env['xma_project.xma_project'].search([]),
#         })

#     @http.route('/xma_project/xma_project/objects/<model("xma_project.xma_project"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('xma_project.object', {
#             'object': obj
#         })
