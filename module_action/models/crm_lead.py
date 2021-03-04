# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class CrmLeadActionCom(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    # @api.depends('next_activity_id')
    def get_nb_action(self):
        print( "[%s] our crm.lead get_nb_action" % __name__)

        action_env = self.env['crm_yziact.action']
        for lead in self:
            action_count = action_env.search([('lead_id', '=', lead.id)])
            print( 'ACTION COUNT RESULT : ', action_count)
            print( 'LEN ACTION COUNT', len(action_count))

            lead.action_count = len(action_count)

    action_id = fields.Integer('Action id')
    action_count = fields.Integer('Action', compute=get_nb_action)

    @api.multi
    def action_view_action(self):
        action = {
            "type": "ir.actions.act_window",
            "name": "Action Commerciales",
            "res_model": "crm_yziact.action",
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            "domain": [('lead_id', '=', self.id)],
            "context": {
                'lead_id': self.id,
                'search_default_lead_id': self.id,
                'default_company_id': self.partner_id.id,
                'default_regarding': 'lead',
            },
            'views_id': {'ref': "crm_yziact.action_com_tree"},
            "target": 'current',
        }
        return action

    @api.multi
    def log_next_activity_done(self):
        action_env = self.env['crm_yziact.action']

        for lead in self:
            contact = None
            partner = lead.partner_id

            # if partner:
            type = lead.next_activity_id
            date = lead.date_action
            desc = lead.title_action
            name = type.name + " : " + partner.name if partner else type.name

            if lead.contact_name:
                contact_obj = self.env['res.partner'].search(
                    [('name', '=', self.contact_name), ('parent_id', '=', partner.id)], limit=1)

                if contact_obj:
                    contact = contact_obj.id

            res=action_env.create({
                    'name': name,
                    'regarding': 'lead',
                    'lead_id': lead.id,
                    'type': type.id,
                    'company_id': partner.id,
                    'date': date,
                    'description': desc,
                    'contact_id': contact
                })
            lead.action_id = res.id

    @api.multi
    def action_done_action(self):
        for lead in self:
            action_env = self.env['crm_yziact.action']
            action_obj = action_env.browse(lead.action_id)
            action_obj.write({'status':'done'})

            lead.write({'next_activity_id':False,
            'date_action':False,
            'title_action':False,
            'action_id': 0,
            })


    # @api.model
    # def retrieve_yzi_action_dashboard(self):
    @api.model
    def retrieve_action_dashboard(self):
        """
        Reprise du code cherchant les donnees du TdB pour le refaire a identique
        Sur le nouveau modele des crm_yzi.action

        """
        result = {
            'meeting': {
                'today': 0,
                'next_7_days': 0,
            },
            'activity': {
                'today': 0,
                'overdue': 0,
                'next_7_days': 0,
            },
            'closing': {
                'today': 0,
                'overdue': 0,
                'next_7_days': 0,
            },
            'done': {
                'this_month': 0,
                'last_month': 0,
            },
            'won': {
                'this_month': 0,
                'last_month': 0,
            },
            'nb_opportunities': 0,
        }

        opportunities = self.search([('type', '=', 'opportunity'), ('user_id', '=', self._uid)])

        # on garde les opp a cloturer et les gagnees
        for opp in opportunities:
            ## cette partie concerne les retard et cloture opp. on laisse tel quel
            if opp.date_deadline:
                date_deadline = fields.Date.from_string(opp.date_deadline)
                if date_deadline == date.today():
                    result['closing']['today'] += 1
                if date.today() <= date_deadline <= date.today() + timedelta(days=7):
                    result['closing']['next_7_days'] += 1
                if date_deadline < date.today():
                    result['closing']['overdue'] += 1

            # Won in Opportunities
            if opp.date_closed:
                date_closed = fields.Date.from_string(opp.date_closed)
                if date.today().replace(day=1) <= date_closed <= date.today():
                    if opp.planned_revenue:
                        result['won']['this_month'] += opp.planned_revenue
                elif date.today() + relativedelta(months=-1, day=1) <= date_closed < date.today().replace(
                        day=1):
                    if opp.planned_revenue:
                        result['won']['last_month'] += opp.planned_revenue

        result['nb_opportunities'] = len(opportunities)
        actions = self.env['crm_yziact.action'].search([('user_id', '=', self._uid)])

        for yzi_act in actions:
            if yzi_act.date:
                date_test = fields.Date.from_string(yzi_act.date)

                if yzi_act.status in ['planned', 'running']:
                    # Next yzi_action
                    if date_test == date.today():
                        result['activity']['today'] += 1
                    if date.today() <= date_test <= date.today() + timedelta(days=7):
                        result['activity']['next_7_days'] += 1
                    if date_test < date.today():
                        result['activity']['overdue'] += 1
                if yzi_act.status in ['done']:
                    if date.today().replace(day=1) <= date_test <= date.today():
                        result['done']['this_month'] += 1
                    elif date.today() + relativedelta(months=-1, day=1) <= date_test < date.today().replace(day=1):
                        result['done']['last_month'] += 1

        # Meetings
        min_date = fields.Datetime.now()
        max_date = fields.Datetime.to_string(datetime.now() + timedelta(days=8))

        meetings_domain = [
            ('start', '>=', min_date),
            ('start', '<=', max_date),
            ('partner_ids', 'in', [self.env.user.partner_id.id])
        ]
        meetings = self.env['calendar.event'].search(meetings_domain)

        for meeting in meetings:
            if meeting['start']:
                start = datetime.strptime(meeting['start'], '%Y-%m-%d %H:%M:%S').date()
                if start == date.today():
                    result['meeting']['today'] += 1
                if date.today() <= start <= date.today() + timedelta(days=7):
                    result['meeting']['next_7_days'] += 1

        result['done']['target'] = self.env.user.target_sales_done
        result['won']['target'] = self.env.user.target_sales_won
        result['currency_id'] = self.env.user.company_id.currency_id.id

        return result

"""
class ActivityLog(models.TransientModel):
    _inherit = "crm.activity.log"

    note = fields.Text()

    @api.multi
    def action_log(self):

        action_env = self.env['crm_yziact.action']
        # self.update()

        context = self._context
        print(context)
        lead_id = context.get('active_id')
        print("LEAD ID", lead_id)

        if not lead_id:
            raise UserError("No Lead Id in Context /!\ ")
        lead_obj = self.env['crm.lead'].browse(lead_id)


        contact = None
        partner = lead_obj.partner_id

        # if partner:
        type = self.next_activity_id
        date = self.date_action
        desc = self.title_action
        name = type.name + " : " + partner.name if partner else type.name

        if self.note :
            desc += " : \n" + self.note



        if lead_obj.contact_name:
            contact_obj = self.env['res.partner'].search(
                [('name', '=', self.contact_name), ('parent_id', '=', partner.id)], limit=1)

            if contact_obj:
                contact = contact_obj.id


        action_env.create({
            'name': name,
            'regarding':'lead',
            'lead_id': lead_id,
            'type': type.id,
            'company_id': partner.id,
            'date': date,
            'description': desc,
            'contact_id': contact
        })

        res = super(CrmLeadActionCom, self).log_next_activity_done()

        return res
"""
