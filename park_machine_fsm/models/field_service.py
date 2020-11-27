# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Task(models.Model):
    _inherit = 'project.task'

    lot_id = fields.Many2one(string="Lot/Serial", comodel_name='stock.production.lot')
    ticket_id = fields.Many2one(comodel_name='helpdesk.ticket')

