# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ticket_id = fields.Many2one(string="Ticket", comodel_name='helpdesk.ticket')

    def action_ticket(self):
        action = {
            'name': "View ticket",
            'type': "ir.actions.act_window",
            'target': 'current',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'res_id': self.ticket_id,
            'view_id': self.env.ref('helpdesk.helpdesk_ticket_view_form').id,
        }

        return action
