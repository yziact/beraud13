# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    tickets_count = fields.Integer(compute="_compute_tickets_count")

    def _compute_tickets_count(self):
        for lot in self:
            ticket_env = self.env['helpdesk.ticket']
            ticket_ids = ticket_env.search([('lot_id', '=', self.id)])
            lot.tickets_count = len(ticket_ids)

    def action_ticket_ids(self):

        action = {
            'name': "Intervention",
            'type': "ir.actions.act_window",
            'target': 'current',
            'view_type': 'form',
            'views': [[False, "list"], [False, "form"]],
            'res_model': 'helpdesk.ticket',
            'view_id': self.env.ref('helpdesk.helpdesk_ticket_view_form').id,
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'default_partner_id': self.partner_id.id
            }
        }

        return action
