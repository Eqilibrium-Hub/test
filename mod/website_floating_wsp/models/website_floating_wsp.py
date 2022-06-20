# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).#

from odoo import api, fields, models, tools

class WebsiteFloatingWsp(models.Model):
    _name = 'website_floating_wsp'
    _description = 'Floating Whatsapp'

    
    name = fields.Char(string='Name',required=False)
    phone = fields.Char('Phone', required=True)
    message = fields.Char('Message', default=' ', )
    position = fields.Selection([('left', 'Left'), ('right', 'Right')], default='left', String='Selection')
    popup_message = fields.Char('Popup Message', default=' ')
    show_popup = fields.Boolean('Show Popup', defaut=True,)
    auto_open_timeout = fields.Integer('Auto Open Time Out', default=0, )
    header_title = fields.Char('Header Title', default='WhatsApp Chat', )
    size = fields.Char('Size', default='72px',)
    website_ids = fields.One2many(
        comodel_name='website',
        inverse_name='floating_wsp_id',
        string='Website',
        required=False)
