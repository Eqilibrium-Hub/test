# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Subscription(models.Model):
    _name = 'xma.subscription'
    _description = 'Subscription'
    _order = "name"

    name = fields.Char(
        string="Name", 
        index=True, 
        required=True, 
        track_visibility="onchange"
    )
    active = fields.Boolean(
        default=True, 
        help="If the active field is set to False, it will allow you to hide the project without removing it."
    )
    sequence = fields.Integer(
        default=10, 
        help="Gives the sequence order when displaying a list of Projects."
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string="Customer", 
        auto_join=True, 
        track_visibility="onchange"
    )