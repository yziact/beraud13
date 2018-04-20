# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from datetime import datetime

class SaleOrderActionCom(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_nb_action(self):
        print( "[%s] our sale.order get_nb_action" % __name__)

        action_env = self.env['crm_yziact.action']
        for sale in self:
            action_count = action_env.search([('sale_id', '=', sale.id)])
            sale.action_count = len(action_count)

    action_count = fields.Integer('Action', compute=get_nb_action)

    @api.multi
    def action_view_action(self):
        action = {
            "type": "ir.actions.act_window",
            "name": "Action Commerciales",
            "res_model": "crm_yziact.action",
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            "domain": [('sale_id', '=', self.id), ('company_id','=', self.partner_id.id)],
            "context": {
                'sale_id': self.id,
                'regarding': 'sale',
                'search_default_sale_id': self.id,
                'default_company_id': self.partner_id.id,
                'default_lead_id': self.opportunity_id.id,
            },
            'views_id': {'ref': "crm_yziact.action_com_tree"},
            "target": 'current',
        }
        return action
