# -*- coding: utf-8 -*-

from odoo import models, fields, api

#Debug
import logging

_logger = logging.getLogger(__name__)


class opentech_caldav(models.Model):
    _inherit = 'calendar.event'

    ics = fields.Text()
