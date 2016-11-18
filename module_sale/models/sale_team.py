# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


# from openerp.osv import fields, osv
# from openerp import SUPERUSER_ID
from openerp import models, api, fields


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    member_ids = fields.Many2many('res.users', string='Team Members')
    """  Requete a executer si la table de relation ne se creer pas

       CREATE TABLE crm_team_res_users_rel
    (
      res_users_id integer NOT NULL,
      crm_team_id integer NOT NULL,
      CONSTRAINT crm_team_res_users_rel_users_id_fkey FOREIGN KEY (res_users_id)
          REFERENCES res_users (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE CASCADE,
      CONSTRAINT crm_team_res_users_rel_rel_team_id_fkey FOREIGN KEY (crm_team_id)
          REFERENCES crm_team (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE CASCADE
    )
    WITH (
      OIDS=FALSE
    );
    ALTER TABLE crm_team_res_users_rel
      OWNER TO odoo;
      """

    def _get_default_team_id(self, cr, uid, context=None, user_id=None):
        print context
        if context is None:
            context = {}
        if 'default_team_id' in context:
            print 'context', context['default_team_id']
            return context['default_team_id']
        if user_id is None:
            user_id = uid
        team_ids = self.search(cr, uid, ['|', ('user_id', '=', user_id), ('member_ids', '=', user_id)])
        print 'team_ids', team_ids
        team_id = team_ids[0] if team_ids else False
        if not team_id and context.get('default_team_id'):
            team_id = context['default_team_id']
        if not team_id:
            team_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'sales_team.team_sales_department')
            print 'team', team_id
        return team_id
