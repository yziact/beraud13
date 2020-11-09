# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def action_task_ids(self):
        action = {
            'name': "Interventions",
            'type': "ir.actions.act_window",
            'target': 'current',
            'view_type': 'form',
            'views': [[False, "list"], [self.env.ref("park_machine_fsm.park_machine_inherit_form_fsm").id, "form"]],
            'res_model': 'project.task',
            'view_id': self.env.ref('industry_fsm.project_task_action_fsm').id,
            'domain': [('is_fsm', '=', True), ('id', 'in', self.task_ids.ids), ('lot_id', '=', self.id)],
            'context': {
                'fsm_mode': True,
                'default_lot_id': self.id,
                'default_partner_id': self.partner_id.id
            }
        }

        return action
