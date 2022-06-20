# -*- coding: utf-8 -*-
from odoo import fields, models


class Project(models.Model):
    _inherit = 'project.project'

    xmasubscription_id = fields.Many2one(
        'xmarts.subscription',
        string="Subscription",
        requerid=True
    )
    native_modules = fields.Char(
        string="Native Modules",
        required=True
    )
    develop_modules = fields.Char(
        string="Develop Modules",
        requerid=True
    )
    thirdpart_modules = fields.Char(
        string="Third Part Modules",
        required=True
    )
    reports = fields.Integer(
        string="Included Reports",
        required=True
    )
    estimated_time = fields.Integer(
        string="Estimated Time",
        required=True
    )
    user_number = fields.Integer(
        string="User Number",
        track_visibility="onchange",
        required=True
    )
    odoo_license = fields.Selection(
        [
            ('community','Community'), 
            ('enterprise','Enterprise')
        ],
        string="Odoo License",
        required=True
    )
    server_id = fields.Many2one(
        'xmarts.server',
        string="Server",
        required=True
    )
    metodology = fields.Selection(
        [
            ('pmp','PMP'), 
            ('qs','QuickStart'), 
            ('upd','Update'), 
            ('sup','Support')
        ],
        string="Metodology",
        default='pmp',
        required=True
    )
    consultan_hours = fields.Integer(
        string="Consultan Hours",
        required=True
    )
    develop_hours = fields.Integer(
        string="Develop Hours",
        required=True
    )
    companys = fields.Integer(
        string="Companys",
        required=True
    )
    observations = fields.Char(
        string="Observations",
        required=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Client Project Leader",
        required=True
    )
    office = fields.Selection(
        [
            ('cdmx', 'CDMX')
        ],
        string="Office",
        default='cdmx'
    )
    is_paid_out = fields.Boolean(string="Is Paid Out?")
    sale_id = fields.Many2one(
        'sale.order', 
        string="Sale Order"
    )
    payment_term_id_rel = fields.Many2one(
        string="Payment Terms", 
        related="sale_id.payment_term_id"
    )
    project_status = fields.Selection(
        [
            ('3.2.', '3.2. Configuración de módulos')
        ],
        string="Project Status",
        default='3.2.'
    )
    payment_notes = fields.Text(string="Payment Notes")

    