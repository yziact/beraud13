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

class stock_parc_machine(models.Model):
    _name = 'parc_machine'

    name = fields.Char()
    product_id = fields.Many2one(
        'product.product',
        'Produit',
        domain="[('categ_id','!=', False), ('categ_id.is_machine','=',True)]"
    )
    lot_id = fields.Many2one('stock.production.lot', 'Lot', domain="[('product_id', '=', product_id)]")
    partner_id = fields.Many2one('res.partner', 'Client', domain="[('customer','=', True)]")
    location_id = fields.Many2one('stock.location', 'Emplacement', domain="[('usage', 'in', ('internal','customer'))]")
    company_id = fields.Many2one('res.company', u'Société')
    quant_id = fields.Many2one('stock.quant', domain="[('product_id', '=', product_id)]")
    date_prod = fields.Date('Date de mise en production')
    date_guarantee = fields.Date('Date de fin de garantie', compute="get_guarantee", inverse="get_prod")
    quantity = fields.Float(u'Quantité totale', digits=dp.get_precision('Product Unit of Measure'))

    @api.model
    def create(self, vals):
        """
        part_name = ""
        prod_name = ""

        if 'partner_id' in vals:
            part_name = vals['partner_id'].name[:5]

        if 'product_id' in vals :
            prod_name = vals['product_id'].name[:5]

        vals['name'] = part_name + " " + prod_name
        """
        print vals

        quant_obj = self.env['stock.quant']

        #par defaut la localisation est celle du client pour la reprise de donnees
        loc = 9
        vals['quantity'] = 1
        if 'location_id' in vals and vals['location_id']:
            loc = vals['location_id']
        else:
            vals['location_id'] = loc

        quant_id = quant_obj.create(
            {
                'product_id': vals['product_id'],
                'lot_id': vals['lot_id'],
                'location_id': loc,
                'qty': vals['quantity'],
            })
        vals['quant_id'] = quant_id.id

        res = super(stock_parc_machine, self).create(vals)

        return res


    @api.multi
    @api.depends('date_prod')
    def get_guarantee(self):

        for item in self:
            if item.date_prod and item.product_id:
                delta = item.product_id.warranty
                date_mise_prod = datetime.strptime(item.date_prod, '%Y-%m-%d')
                month = int(delta) + date_mise_prod.month
                days = int(str(delta).split('.')[1])

                # gestion des demi mois uniquement
                if days == 5:
                    days = 15
                else:
                    days = 0

                relativedelta = rd(months=month, days=days)
                date_guarantee = date_mise_prod + relativedelta

                item.update({'date_guarantee': datetime.strftime(date_guarantee, '%Y-%m-%d')})

    @api.multi
    @api.depends('date_guarantee')
    def get_prod(self):

        for item in self:
            if item.date_guarantee and item.product_id:
                delta = item.product_id.warranty
                guarantee = datetime.strptime(item.date_guarantee, '%Y-%m-%d')
                month = int(delta) + guarantee.month
                days = int(str(delta).split('.')[1])

                # gestion des demi mois uniquement
                if days == 5:
                    days = 15
                else:
                    days = 0

                relativedelta = rd(months=month, days=days)
                date_prod = guarantee - relativedelta

                item.update({'date_prod': datetime.strftime(date_prod, '%Y-%m-%d')})
