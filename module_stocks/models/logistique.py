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
        # tools.sql.drop_view_if_exists(cr, 'stock_view_logistique')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_view_logistique AS
            (
               SELECT row_number() OVER(win) as id,
               SUM(qty) as quantity,
               (
                   SELECT SUM(qty) FROM stock_quant
                    WHERE reservation_id IS NOT NULL
                    AND (lot_id = q.lot_id OR lot_id IS NULL)
                    AND product_id = q.product_id
                    AND location_id = q.location_id
                    AND company_id = q.company_id
               ) as reserved_quantity,
               q.lot_id,
               q.product_id,
               q.company_id,
               q.location_id
               FROM stock_quant q
                LEFT JOIN stock_location l ON l.id = q.location_id
                LEFT JOIN product_product p ON p.id = q.product_id
                LEFT JOIN product_template t ON t.id = p.product_tmpl_id
               WHERE l.usage = 'internal' AND t.type = 'product'
                GROUP BY q.lot_id, q.product_id, q.company_id, q.location_id
                HAVING SUM(qty) >= 0.00000001 OR SUM(qty) <= -0.00000001
               WINDOW win AS (ORDER BY MIN(lot_id))
            )
        """)
