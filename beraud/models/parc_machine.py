# -*- encoding: UTF-8 -*-

from openerp import api, models, fields
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta as rd

class stock_view_parc(models.Model):
    _name = 'stock.view.parc'
    _auto = False

    id = fields.Integer('ID')
    product_id = fields.Many2one('product.product', 'Produit')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    partner_id = fields.Many2one('res.partner', 'Client')
    location_id = fields.Many2one('stock.location', 'Emplacement')
    company_id = fields.Many2one('res.company', u'Société')

    quantity = fields.Float(u'Quantité totale', digits=dp.get_precision('Product Unit of Measure'))

    def init(self, cr):
        # tools.sql.drop_view_if_exists(cr, 'stock_view_logistique')

        cr.execute("""
        CREATE OR REPLACE VIEW stock_view_parc AS (
           SELECT row_number() OVER(win) as id,
               SUM(qty) as quantity,
               m.partner_id,
               p.lot_id,
               p.product_id,
               p.company_id,
               p.location_id
           FROM stock_quant p
           LEFT JOIN stock_quant_move_rel r ON r.quant_id = p.id
           LEFT JOIN stock_move m ON m.id = r.move_id
           LEFT JOIN stock_location l ON l.id = p.location_id
           WHERE ((l.usage = 'customer' AND m.location_dest_id = l.id) AND  (m.id = r.move_id AND p.id = r.quant_id) )
           GROUP BY p.lot_id, p.product_id, p.company_id, p.location_id, m.partner_id
           HAVING SUM(qty) >= 0.00000001 OR SUM(qty) <= -0.00000001
           WINDOW win AS (ORDER BY MIN(lot_id))
        )
        """)

class StockParcMachine(models.Model):
    _name = 'parc_machine'

    # @api.depends('partner_id', 'product_id')
    def _compute_name(self):
        print 'GET NAME'
        name = ""
        if self.partner_id and self.product_id :
            name = self.partner_id.name + ' : ' + self.product_id.name

        print name
        self.name = name

    name = fields.Char(string="Name", compute='_compute_name')
    product_id = fields.Many2one(
        'product.product',
        'Produit',
        domain="[('categ_id','!=', False), ('categ_id.is_machine','=',True)]"
    )
    lot_id = fields.Many2one('stock.production.lot', 'Lot', domain="[('product_id', '=', product_id)]")
    partner_id = fields.Many2one('res.partner', 'Client', domain="[('customer','=', True)]")
    location_id = fields.Many2one('stock.location', 'Emplacement quant', domain="[('usage', 'in', ('internal','customer'))]")
    company_id = fields.Many2one('res.company', u'Société')
    quant_id = fields.Many2one('stock.quant', string='Quant',domain="[('product_id', '=', product_id)]")
    date_prod = fields.Date('Date de mise en production', store=True)
    date_guarantee = fields.Date('Date de fin de garantie', compute="get_guarantee",inverse="get_prod", store=True)
    quantity = fields.Float(u'Quantité totale', digits=dp.get_precision('Product Unit of Measure'))
    cm = fields.Boolean(string="Contrat de maintenance")
    location_partner = fields.Many2one('res.partner', string=u"Emplacement clients", domain="['|',('id', '=', partner_id), '&', ('type','=','delivery'), ('parent_id','=',partner_id)]")

    @api.model
    def create(self, vals):
        print vals.keys()
        quant_obj = self.env['stock.quant']

        #par defaut la localisation est celle du client pour la reprise de donnees
        loc = 9
        vals['quantity'] = 1
        if 'location_id' in vals and vals['location_id']:
            loc = vals['location_id']
        else:
            vals['location_id'] = loc

        if not 'quant_id' in vals:
            quant_id = quant_obj.create(
                {
                    'product_id': vals['product_id'],
                    'lot_id': vals['lot_id'],
                    'location_id': loc,
                    'qty': vals['quantity'],
                })
            vals['quant_id'] = quant_id.id

        res = super(StockParcMachine, self).create(vals)
        return res

    @api.multi
    @api.depends('date_prod')
    def get_guarantee(self):

        for item in self:
            if item.date_prod and item.product_id and not item.date_guarantee:
                delta = item.product_id.warranty
                date_mise_prod = datetime.strptime(item.date_prod, '%Y-%m-%d')
                month = int(delta)
                days = int(str(delta).split('.')[1])

                # gestion des demi mois uniquement
                if days == 5:
                    days = 15
                else:
                    days = 0

                relativedelta = rd(months=month, days=days)
                date_guarantee = date_mise_prod + relativedelta

                item.update({'date_guarantee': datetime.strftime(date_guarantee, '%Y-%m-%d')})

    def get_prod(self):
        return True


    @api.one
    def fix_me(self):
        cm_env = self.env['sale.subscription']
        move_env = self.env['stock.move']
        move_ids = move_env.search([('product_id.categ_id.is_machine', '=', True), ('location_dest_id', '=', 9), ('partner_id', '!=', False)])

        for move in move_ids:
            cm = False
            partner_mov = move.partner_id
            parent_partner = partner_mov.parent_id.id

            cm_obj = cm_env.search(['|', ('partner_id', '=', parent_partner), ('partner_id', '=', partner_mov.id)])

            if cm_obj:
                cm = True

            for quant in move.quant_ids:
                i = 0
                while i < quant.qty:
                    self.create({
                        'partner_id':parent_partner or partner_mov.id,
                        'location_partner': partner_mov.id,
                        'cm': cm,
                        'quant_id': quant.id,
                        'product_id': quant.product_id.id,
                        'lot_id': quant.lot_id.id or False,
                        'location_id': quant.location_id.id,
                        'company_id': move.company_id.id,
                        'quantity': 1.0,
                        'date_prod': move.date
                    })
                    i += 1


    @api.multi
    def action_issue(self):
        self.ensure_one()
        project_env = self.env['project.project']
        user_env = self.env['res.users']
        client = ''
        company = ''
        machine = ''
        lot_id = ''
        context = {}

        if self.partner_id:
            client = self.partner_id.id
            company = self.partner_id.company_id.id

        if self.product_id:
            machine = self.product_id.id

        if self.lot_id:
            lot_id = self.lot_id.id

        if not company:
            user = user_env.browse(self._uid)
            company = user.company_id.id

        project = project_env.search([('name', '=', 'SAV'), ('company_id', '=', company)])

        context={
            'search_default_parc_rec': self.id,
            'default_parc_rec': self.id,
            'search_default_project_id': project.id,
            'default_project_id': project.id,
            'search_default_company_id': company,
            'default_company_id': company,
            'search_default_partner_id': client,
            'default_partner_id':client,
            'default_lot_id': lot_id,
            'search_default_product_id': machine,
            'default_product_id':machine
        }

        print context


        action = {
            'type': u'ir.actions.act_window',
            'name': u'Historique des Incidents',
            'res_model': u'project.issue',
            'view_type': 'form',
            'views': [[False, "kanban"],[False, "form"]],
            'context': context,
            'target': u'current',

        }

        return action


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    parc_rec = fields.Many2one('parc_machine', string='Parc Machine')
    lot_id = fields.Many2one('stock.production.lot', u'n°Série')
    product_id = fields.Many2one('product.product', u'Machine', domain="[('categ_id','!=', False), ('categ_id.is_machine','=',True)]")

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        parc_env = self.env['parc_machine']

        for move in self:
            if move.product_id.categ_id.is_machine:
                if move.location_dest_id.id == 9:
                    partner_id = move.partner_id.id or move.picking_partner_id.id

                    if move.partner_id.type == 'delivery':
                        partner_id = move.partner_id.parent_id.id

                    for quant in move.quant_ids:
                        parc_rec = parc_env.search([('quant_id', '=', quant.id)])

                        if parc_rec:
                            print 'parc trouver'
                            parc_rec.update({
                                'location_id': move.location_dest_id.id,
                                'partner_id': move.partner_id.id or move.picking_partner_id.id
                            })

                        else:
                            i = 0
                            while i < quant.qty:
                                parc_env.create({
                                    'partner_id': partner_id,
                                    'quant_id': quant.id ,
                                    'product_id': quant.product_id.id,
                                    'lot_id': quant.lot_id.id or False,
                                    'location_id': quant.location_id.id,
                                    'company_id': move.company_id.id,
                                    'quantity': 1.0,
                                    'date_prod': move.date,
                                    'location_partner': move.partner_id.id or move.picking_partner_id.id
                                })
                                i += 1

        return res
