# -*- coding: UTF-8 -*-

from openerp import api, models, fields
import openerp.addons.decimal_precision as dp

class stock_view_logistique(models.Model):
    _name = 'stock.view.logistique'
    _auto = False

    id = fields.Integer('ID')
    product_id = fields.Many2one('product.product', 'Produit')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    location_id = fields.Many2one('stock.location', 'Emplacement')
    company_id = fields.Many2one('res.company', u'Société')
    quantity = fields.Float(u'Quantité totale', digits=dp.get_precision('Product Unit of Measure'))
    reserved_quantity = fields.Float('Quantité réservée', digits=dp.get_precision('Product Unit of Measure'))
    # reservations = fields.Many2many('stock.move', 'Réservations', compute='_get_reservations')

    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'stock_view_logistique')
        cr.execute("""
        CREATE OR REPLACE VIEW stock_view_logistique AS (
           SELECT row_number() OVER(win) as id,
           SUM(qty) as quantity,
           (SELECT SUM(qty) FROM stock_quant
            WHERE reservation_id IS NOT NULL
            AND (lot_id = p.lot_id OR lot_id IS NULL)
            AND product_id = p.product_id
            AND location_id = p.location_id
            AND company_id = p.company_id) as reserved_quantity,
           p.lot_id,
           p.product_id,
           p.company_id,
           p.location_id FROM stock_quant p
           LEFT JOIN stock_location l ON l.id=p.location_id
           WHERE l.usage = 'internal'
           GROUP BY p.lot_id, p.product_id, p.company_id, p.location_id
           HAVING SUM(qty) >= 0.00000001 OR SUM(qty) <= -0.00000001
           WINDOW win AS (ORDER BY MIN(lot_id))
        )
        """)


    # valorisation = fields.Float('Valorisation', compute='_get_valorisation')
    # dluo_state = fields.Selection([('ok', 'OK'), ('warn', 'Attention'), ('alert', 'Alerte')], string='Etat DLUO', compute='_get_dluo_state')

    # @api.multi
    # def _get_dluo_state(self):
    #     for line in self:
    #         if line.lot_id.use_date:
    #             dluo = datetime.datetime.strptime(line.lot_id.use_date, "%Y-%m-%d %H:%M:%S")
    #             # Si DLUO < now : alerte
    #             if dluo < datetime.datetime.now():
    #                 line.dluo_state = 'alert'
    #             else:
    #                 if line.product_id.use_time:
    #                     # Si delta (dluo - now) < product_use_days
    #                     delta_days_produit = datetime.timedelta(days=line.product_id.use_time)
    #                     delta_days_dluo = dluo - datetime.datetime.now()
    #                     if (int(delta_days_dluo.days) < (int(delta_days_produit.days) / 2)):
    #                         line.dluo_state = 'warn'
    #                     else:
    #                         line.dluo_state = 'ok'
    #                 else:
    #                     line.dluo_state = 'ok'
    #         else:
    #             line.dluo_state = 'ok'


    # @api.multi
    # def _get_valorisation(self):
    #     def clean_char(data):
    #         try :
    #             return float(data.replace(',','.'))
    #         except:
    #             # Trucs bizzares from LSI, genre ' '
    #             return 0
    #
    #     for line in self:
    #         # Calcul du prix
    #         if not line.product_id.standard_price:
    #             line.valorisation = clean_char(line.product_id.ext_qual_pmp) * line.quantity
    #         else :
    #             line.valorisation = line.product_id.standard_price * line.quantity

    # @api.one
    # def _get_reservations(self):
    #     print "_get_reservations"
    #     q_obj = self.env['stock.quant']
    #     MV_IDS = []
    #
    #     for quant in q_obj.search([('lot_id','=',self.lot_id.id),
    #                                ('location_id','=',self.location_id.id),
    #                                ('reservation_id','!=',False)]):
    #
    #         if not quant.reservation_id.id in MV_IDS:
    #             MV_IDS.append(quant.reservation_id.id)
    #             self.reservations += quant.reservation_id


