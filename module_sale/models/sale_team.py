# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from openerp.osv import fields, osv


class CrmTeam(osv.Model):
    _inherit = "crm.team"

    def _get_default_team_id(self, cr, uid, context=None, user_id=None):
        if context is None:
            context = {}
        if 'default_team_id' in context:
            return context['default_team_id']
        if user_id is None:
            user_id = uid
        team_ids = self.search(cr, uid, ['|', ('user_id', '=', user_id), ('member_ids', '=', user_id)], limit=1, context=context)
        team_id = team_ids[0] if team_ids else False
        if not team_id and context.get('default_team_id'):
            team_id = context['default_team_id']
        if not team_id:
            team_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'sales_team.team_sales_department')
        return team_id
