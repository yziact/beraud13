# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    lot_id = fields.Many2one(string="Lot/Serial", comodel_name='stock.production.lot')
