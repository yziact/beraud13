# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    lot_id = fields.Many2one(string="Lot/Serial", comodel_name='stock.production.lot')

    def action_park_machine(self):
        action = {
            'name': "Parc Machine",
            'type': "ir.actions.act_window",
            'target': 'current',
            'view_type': 'form',
            'views': [
                [self.env.ref('park_machine.pm_machine_tree').id, "list"],
                [self.env.ref('park_machine.pm_machine_form').id, "form"]
            ],
            'res_model': 'stock.production.lot',
            'view_id': self.env.ref('park_machine.pm_machine_tree').id,
            # 'domain': [('lot_id', '=', self.id)], # Last chance, first, try auto-filtered
            'context': {
                'search_default_name': self.lot_id.name,
            }
        }

        return action
