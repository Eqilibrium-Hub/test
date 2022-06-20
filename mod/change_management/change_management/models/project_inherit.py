# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectInherit(models.Model):
    _inherit = 'project.project'

    change_request_ids = fields.One2many(
        'change.request',
        'project_id',
        string='Solicitudes de Cambio'
        )

    change_count = fields.Integer(
        compute="_compute_change_count",
        string="Change Count"
        )

    arrears_request_ids = fields.One2many(
        'arrears.request', 
        'project_id',
        string='Solicitudes de Cambio'
        )

    arrears_count = fields.Integer(
        compute="_compute_arrears_count",
        string="arrears Count"
        )

    @api.depends('change_request_ids')
    def _compute_change_count(self):
        for value in self:
            value.change_count=0
            if value.change_request_ids:
                value.change_count = len(value.change_request_ids)

    @api.depends('arrears_request_ids')
    def _compute_arrears_count(self):
        for value in self:
            value.arrears_count = 0
            if value.arrears_request_ids:
                value.arrears_count = len(value.arrears_request_ids)



