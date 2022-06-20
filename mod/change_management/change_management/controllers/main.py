# -*- coding: utf-8 -*-

import werkzeug

from odoo import fields, http, _
from odoo.http import request

class ChangeRequest(http.Controller):

    @http.route('/changes/<int:order_id>/<token>', auth="public", website=True)
    def get_view(self, order_id, token=None,message=False):
        now = fields.Date.today()
        if token:
            request_id = request.env['change.request'].sudo().search([('id', '=', order_id), ('access_token', '=', token)])
        else:
            request_id = request.env['change.request'].search([('id', '=', order_id)])

        if not request_id:
            return (404, [], None)
        return request.render("change_management.view_change_request_web",{
            'request_id': request_id,
            'message': message and int(message) or False
            })

    @http.route(['/changes/<int:order_id>/<token>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def decline(self, order_id, token, **post):
        request_id = request.env['change.request'].sudo().browse(order_id)
        if token != request_id.access_token:
            return (404, [], None)
        if request_id.state != "Enviado":
            return (404, [], None)
        request_id.action_rejected()
        message = post.get('decline_message')
        message = "Motivo de la cancelacion <br/>" + message
        if message:
            request_id.message_post(body=message, subtype="mt_comment")
        return request.redirect("/changes/%s/%s?message=2" % (order_id, token))

    @http.route(['/changes/accept'], type='json', auth="public", website=True)
    def accept(self, order_id, token=None, signer=None, sign=None, **post):
        request_id = request.env['change.request'].sudo().browse(order_id)
        if token != request_id.access_token:
            return (404, [], None)
        if request_id.state != "Enviado":
            return (404, [], None)
        attachments = [('signature.png', sign.decode('base64'))] if sign else []
        request_id.action_acepted()
        message = _('Order signed by %s') % (signer,)
        request_id.message_post(body=message, subtype="mt_comment", attachments="attachments")
        return True