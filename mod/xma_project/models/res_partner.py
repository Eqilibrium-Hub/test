# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    odoo_subscription_id = fields.Many2one(
        'xmarts.subscription', 
        string="Odoo Subscription"
    )
