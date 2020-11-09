# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    lot_ids = fields.One2many(comodel_name='stock.production.lot', inverse_name='partner_id')
    lots_count = fields.Integer(compute='_compute_lots_count')

    def _compute_lots_count(self):
        for partner in self:
            partner.lots_count = len(partner.lot_ids)

    def action_lot_ids(self):
        action = {
            'name': "Machines",
            'type': "ir.actions.act_window",
            'target': 'current',
            'view_type': 'form',
            'views': [
                [self.env.ref('park_machine.pm_machine_tree').id, "list"],
                [self.env.ref('park_machine.pm_machine_form').id, "form"]
            ],
            'res_model': 'stock.production.lot',
            'view_id': self.env.ref('park_machine.pm_machine_tree').id,
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'company_id': self.user_id.company_id.id
            }
        }

        return action
