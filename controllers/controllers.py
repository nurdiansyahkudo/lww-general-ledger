# -*- coding: utf-8 -*-
# from odoo import http


# class CustomGl(http.Controller):
#     @http.route('/custom_gl/custom_gl', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_gl/custom_gl/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_gl.listing', {
#             'root': '/custom_gl/custom_gl',
#             'objects': http.request.env['custom_gl.custom_gl'].search([]),
#         })

#     @http.route('/custom_gl/custom_gl/objects/<model("custom_gl.custom_gl"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_gl.object', {
#             'object': obj
#         })

