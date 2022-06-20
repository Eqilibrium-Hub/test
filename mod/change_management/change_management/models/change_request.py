# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
import uuid


class ChangeManagement(models.Model):
    _name = 'change.request'
    _inherit = ['mail.thread']

    sequence = fields.Char(
        string='Folio', 
        required=True, 
        default='New',
        readonly=True)

    project_id = fields.Many2one(
        'project.project',
        string='Proyecto')

    date_request = fields.Date(
        string='Fecha de Solicitud',
        default=fields.Date.today,
        required=True)

    applicant = fields.Many2one(
        'res.partner',
        string="Solicitante",
        required=True)

    priority = fields.Selection(
        selection=[
            ('', ''),
            ('Baja', 'Baja'),
            ('Media', 'Media'),
            ('Alta', 'Alta'),
        ],
        string="Prioridad",default='')
    type_ids = fields.Many2many(
        'change.request.type',
        string='Tipo de Solicitud de Cambio')

    description = fields.Text(
        string='Descripción de Solicitud',
        required=True)

    impact_analysis = fields.Text(
        string='Análisis de Impacto',
        required=True)

    cost_by_day = fields.Float(
        string='Costo por Dia')

    impact_in_days = fields.Integer(
        string='Impacto en Días',
        required=True)

    impact_economic = fields.Float(
        string="Impacto Economico", 
        compute="economic_impact",
        store=True)

    sign_cons = fields.Binary(
        string='Consultor')

    sign_client = fields.Binary(
        string='Cliente')

    acceptance_date = fields.Datetime(
        string='Fecha de Aceptación', 
        readonly=True)

    state = fields.Selection(
        selection=[
            ('Borrador', 'Borrador'),
            ('Enviado', 'Enviado'),
            ('Rechazado', 'Rechazado'),
            ('Aprobado', 'Aprobado'),
        ],
        string="Estado",
        readonly=True,
        default='Borrador',
        track_visibility="onchange")

    access_token = fields.Char(
        'Security Token', 
        copy=False, 
        default=lambda self: str(uuid.uuid4()),
        required=True)

    def open_change(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/changes/%s/%s' % (self.id, self.access_token)
        }

    @api.model
    def create(self, vals):
        if vals.get('sequence','New') == 'New':
            vals['sequence']=self.env['ir.sequence'].next_by_code('change.request') or 'New'
            result = super(ChangeManagement, self).create(vals)
            return result

    @api.depends('cost_by_day','impact_in_days')
    def economic_impact(self):
        for value in self:
            value.impact_economic = 0
            if value.cost_by_day != False and value.impact_in_days != False:
                value.impact_economic = (value.cost_by_day)*(value.impact_in_days)

    def action_acepted(self):
        for value in self:
            value.write({'state': 'Aprobado'})
            value.acceptance_date = datetime.datetime.utcnow()

    def action_rejected(self):
        for value in self:
            print(value)
            value.write({'state': 'Rechazado'})

    def action_send(self):
        template = self.env.ref('change_management.change_request_template')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='change.request',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            force_email=True
        )
        body = "Solicitud enviada" + "\n" + "Proyecto: " + str(self.project_id.name)
        self.message_post(body=body, subtccccype='mt_comment', context="")
        self.write({'state': 'Enviado'})
        return {
            'name': ('Solicitud de Cambio'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


class ChangeType(models.Model):
    _name = 'change.request.type'

    name = fields.Char(string="Nombre", required=True)