# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
import logging
_log = logging.getLogger(__name__)


class Action(models.Model):
    _name = 'crm_yziact.action'
    _inherit = ['mail.thread']
    _description = "Crm Action"
    _order = "date"

    ######DEFAULT####
    def get_user(self):
        uid = self._context.get('uid', False)
        user_id = self.env['res.users'].browse(uid).id

        return user_id

    def get_datetime(self):
        return datetime.now()


    ######SELECTION####
    status = fields.Selection([
        ('planned',u'Plannifiée'),
        ('running', u'En Cours'),
        ('done', u'Terminée')
    ], string='Statut', default='planned')
    regarding = fields.Selection([
        ('lead', 'Piste/Opp'),
        ('company', 'Compte'),
        ('contact', 'Contact'),
        ('sale', 'Vente')
    ], string='Concernant')

    ######TEXT####
    name = fields.Char(string="Nom", track_visibility="always", required=True)
    description = fields.Html(string='Compte rendu')

    ######DATE####
    # date = fields.Datetime(string='Date', default=datetime.now(), compute='date_debut_trigger', inverse='get_true', store=True, required=True,)
    date = fields.Datetime(string='Date debut', default=get_datetime, required=True)
    #to create an rdv and be capable to modifie the dates of both event and action
    date_debut = fields.Datetime(string='Date debut', compute='get_date', inverse='get_true', store=True, related="event_id.start_datetime")
    date_end = fields.Datetime(string='Date fin', compute='get_date', inverse='get_true', store=True, related="event_id.stop")
    #to make a filter on today i need a date without time
    date_filter = fields.Date(string='Date', compute='get_date', store=True)

    ######BOOLEAN####
    active = fields.Boolean(default=True)

    ######RELATIONEL####
    user_id = fields.Many2one(comodel_name='res.users', string=u'Assigné à', default=get_user)
    type = fields.Many2one(comodel_name='crm.activity', track_visibility="always", required=True, delegate=True)
    company_id = fields.Many2one(comodel_name='res.partner', string=u"Société", domain="[('company_type','=','company')]", track_visibility="always")
    contact_id = fields.Many2one(comodel_name='res.partner', string=u"Contact", domain="[('company_type','=','person'), ('parent_id','=',company_id)]")
    sale_id = fields.Many2one(comodel_name='sale.order', string="Vente", domain="['|',('partner_id','=',company_id), ('partner_id','=',contact_id)]", track_visibility="always")
    lead_id = fields.Many2one(comodel_name='crm.lead', string=u"Piste / Opportunité", domain="[('partner_id','=',company_id)]", track_visibility="always")
    event_id = fields.Many2one(comodel_name='calendar.event', string="Rendez-vous", store=True)


    @api.model
    def create(self, vals):
        calendar_env = self.env['calendar.event']
        type_act_env = self.env['crm.activity']
        user_env = self.env['res.users']
        user_obj = user_env.browse(vals.get('user_id', self._uid))
        event = None
        print(vals.get('regarding', False))
        if not vals.get('regarding', False) :
            regard = False

            if vals.get('sale_id', False):
                regard = 'sale'
            elif vals.get('lead_id', False):
                regard = 'lead'
            elif vals.get('contact_id', False):
                regard = 'contact'
            elif vals.get('company_id', False):
                regard = 'company'

            vals['regarding'] = regard

        res = super(Action, self).create(vals)
        date_end = vals.get('date_end',False)
        if not date_end :
            date_end = datetime.strptime(res.date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=1)
            date_end = date_end.strftime('%Y-%m-%d %H:%M:%S')

        type_act =  type_act_env.browse(vals.get('type',False))

        if type_act and type_act.synchro and not vals.get('event_id', False) :
            event = calendar_env.with_context({'no_email':True}).create({
                'name': res.name,
                'partner_ids': [(6, False,[user_obj.partner_id.id])],
                'start':res.date,
                'stop':date_end,
                'start_datetime': res.date,
                'stop_datetime':date_end,
                'description': res.description,
                'action_id':res.id,
            })
            res.event_id = event.id

        if res.company_id:
            res.company_id.change_date_action(res.date)


        return res


    @api.multi
    def unlink(self):
        context = {}

        if self._context:
            context = self._context

        for lead in self:
            if not context.get('event', False):
                if lead.event_id:
                    lead.event_id.with_context(action=True).unlink()
            super(Action, lead).unlink()


    @api.depends('date')
    def get_date(self):
        for action in self:
            action.date_filter = action.date

            if action.date_debut != action.date:
                action.date_debut = action.date

            if not action.date_end or action.date_end < action.date:
                action.date_end = datetime.strptime(action.date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=1)


    def get_true(self):
        return  True

    @api.multi
    @api.onchange('contact_id')
    def append_address(self):

        for rec in self:
            partner = rec.contact_id
            if not partner:
                continue

            existing_desc = '{}\n'.format(rec.description) if rec.description else ''
            rec.description = existing_desc + partner.get_formatted_info()


class PartnerActions(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def get_formatted_address(self):
        self.ensure_one()
        partner = self

        fmt = partner._get_default_address_format()
        address = fmt % {
            'street': partner.street if partner.street else '',
            'street2': partner.street2 if partner.street2 else '',
            'city': partner.city if partner.city else '',
            'state_code': '',
            'zip': partner.zip if partner.zip else '',
            'country_name': partner.country_id.name if partner.country_id else '',
        }

        splt = address.split('\n')
        address = ''.join([x+'\n' for x in splt if x.strip()])

        return address

    @api.multi
    def get_formatted_info(self):
        self.ensure_one()

        fmt = '{}\n'
        info = fmt.format(self.name) if self.name else ''
        info += fmt.format(self.phone) if self.phone else ''
        info += fmt.format(self.mobile) if self.mobile else ''
        info += fmt.format(self.email) if self.email else ''

        address = self.get_formatted_address()
        info += fmt.format(address) if address else ''

        return info

    @api.multi
    def get_nb_action(self):
        action_env = self.env['crm_yziact.action']
        for partner in self:
            action_count = action_env.search([('company_id', '=', partner.id)])
            action_count_active = action_env.search([('company_id', '=', partner.id),('status','!=', 'done')])
            partner.action_count = len(action_count)
            partner.action_count_active = len(action_count_active)

            if action_count:
                action_decroissant = sorted(action_count, key=attrgetter('date'), reverse=True)
                partner.last_action = action_decroissant[0].date

    @api.multi
    def get_contact_nb_action(self):
        print( "[%s] our res.partner get_contact_nb_action" % __name__)
        action_env = self.env['crm_yziact.action']
        for partner in self:
            action_count = action_env.search([('contact_id', '=', partner.id)])
            action_count_active = action_env.search([('contact_id', '=', partner.id),('status','!=','done')])
            partner.contact_action_count = len(action_count)
            partner.contact_action_count_active = len(action_count_active)


    action_count = fields.Integer('Action', compute=get_nb_action)
    action_count_active = fields.Integer('Action', compute=get_nb_action)

    contact_action_count = fields.Integer('Action', compute=get_contact_nb_action)
    contact_action_count_active = fields.Integer('Action', compute=get_contact_nb_action)

    last_action = fields.Date(u'Date dernière action')

    @api.multi
    def action_view_action(self):
        if 'person' in self.company_type:
            action = {
                "type": "ir.actions.act_window",
                "name": "Action Commerciales",
                "res_model": "crm_yziact.action",
                "view_type": 'form',
                "views": [[False, "tree"], [False, "form"]],
                "domain":[('contact_id','=', self.id)],
                "context": {
                    'contact_id': self.id,
                    'search_default_contact_id': self.id,
                    'default_company_id': self.parent_id.id,
                    'default_regarding':'contact',
                },
                'views_id': {'ref': "crm_yziact.action_com_tree"},
                "target": 'current',
            }

        else:
            action = {
                "type": "ir.actions.act_window",
                "name": "Action Commerciales",
                "res_model": "crm_yziact.action",
                "view_type": 'form',
                "views": [[False, "tree"], [False, "form"]],
                "domain": [('company_id', '=', self.id)],
                "context": {'company_id': self.id ,
                            'search_default_company_id': self.id,
                            'default_regarding': 'company',
                            },
                'views_id': {'ref': "crm_yziact.action_com_tree"},
                "target": 'current',
            }

        return action


    def change_date_action(self, date):
        date_action = self.last_action

        if not date_action or date > date_action:
            return self.write({'last_action':date})



class TypeActivity(models.Model):
    _inherit = 'crm.activity'

    synchro = fields.Boolean('Synchro')
