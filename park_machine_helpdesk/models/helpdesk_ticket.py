# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    lot_id = fields.Many2one(string="Lot/Serial", comodel_name='stock.production.lot')

