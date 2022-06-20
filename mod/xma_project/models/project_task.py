# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountAnalyticLine(models.Model):
	_name = 'account.analytic.line'
	_inherit = 'account.analytic.line'

	type_hours = fields.Selection([
		('default','Normal'),
		('bonus','Bonos'),
		('free','Libres'),
		('extra_hours','Horas extras')
		],string="Categoria de horas")