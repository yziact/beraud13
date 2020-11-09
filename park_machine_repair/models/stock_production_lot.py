# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    repairs_count = fields.Integer(compute="_compute_repair_count")

    def _compute_repair_count(self):
        for lot in self:
            repair_env = self.env['repair.order']
            repair_ids = repair_env.search([('lot_id', '=', self.id)])
            lot.repairs_count = len(repair_ids)

    def action_repair_order_ids(self):

        action = {
            'name': "Repairs",
            'type': "ir.actions.act_window",
            'target': 'current',
            'view_type': 'form',
            'views': [[False, "list"], [False, "form"]],
            'res_model': 'repair.order',
            'view_id': self.env.ref('repair.view_repair_order_tree').id,
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_product_id': self.product_id.id,
                'default_lot_id': self.id,
                'default_partner_id': self.partner_id.id
            }
        }

        return action
