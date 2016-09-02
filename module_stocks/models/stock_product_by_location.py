# -*- coding: utf-8 -*-
##############################################
#
# ChriCar Beteiligungs- und Beratungs- GmbH
# Copyright (C) ChriCar Beteiligungs- und Beratungs- GmbH
# all rights reserved
# created 2009-09-19 23:51:03+02
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/> or
# write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
###############################################
#from tools.sql import drop_view_if_exists

from openerp import models, api, fields
from openerp.tools.sql import drop_view_if_exists

import logging 
_logger = logging.getLogger(__name__)

class stock_move_by_location(models.Model):
    _name = "stock_move_by_location"
    _description = "Location Moves"
    _auto = False

    #id: fields.char    ('id',size=16, readonly=True),
    description = fields.Char('Description', size=16, readonly=True)
    location_id = fields.Many2one('stock.location','Location', select=True, readonly=True)
    product_id = fields.Many2one('product.product','Product', select=True, readonly=True)
    categ_id = fields.Char(related='product_id.cated_id', string='Category', readonly=True)
    name = fields.Float('Quantity', digits=(16,2), readonly=True)
    uom_id = fields.Char(related='product_id.uom_id', string="UoM", readonly = True )
    product_qty_pending = fields.Float('Quantity Pending', digits=(16,2), readonly=True)
    date = fields.Datetime('Date Planned', select=True, readonly=True)
    prodlot_id = fields.Many2one('stock.production.lot', 'Production lot', select=True, readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Packing', select=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    #select get_id('stock_product_by_location',l.id,product_id,0),
    def __init__(self, pool, cr):
        drop_view_if_exists(cr, 'stock_product_by_location_prodlot')
        drop_view_if_exists(cr, 'stock_product_by_location')
        drop_view_if_exists(cr, 'stock_move_by_location')
        cr.execute("""create or replace view stock_move_by_location
                         as
                         select i.id ,
                         l.id as location_id,product_id,
                         i.name as description,
                         case when state ='done' then product_qty else 0 end as name,
                         case when state !='done' then product_qty else 0 end as product_qty_pending,
                         date, lot_id,
                         picking_id,l.company_id
                         from stock_location l,
                         stock_move i
                         where l.usage='internal'
                         and i.location_dest_id = l.id
                         and state != 'cancel'
                         and i.company_id = l.company_id
                         union all
                         select -o.id ,
                         l.id as location_id ,product_id,
                         o.name as description,
                         case when state ='done' then -product_qty else 0 end as name,
                         case when state !='done' then -product_qty else 0 end as product_qty_pending,
                         date, lot_id,
                         picking_id,l.company_id
                         from stock_location l,
                         stock_move o
                         where l.usage='internal'
                         and o.location_id = l.id
                         and state != 'cancel'
                         and o.company_id = l.company_id
                         ;""")

stock_move_by_location()

class stock_product_by_location(models.Model):
    _name = "stock_product_by_location"
    _description = "Product Stock Sum"
    _auto = False

    #'id'                 : fields.char    ('id',size=16, readonly=True),
    location_id = fields.Many2one('stock.location','Location', select=True, required=True, readonly=True)
    product_id = fields.Many2one('product.product','Product', select=True, required=True, readonly=True)

    uom_id = fields.Char(related='product_id.uom_id', string="UoM", readonly = True )
    categ_id = fields.Char(related='product_id.categ_id', string="Category",readonly=True)
    cost_method = fields.Char(related='product_id.cost_method', string="Cost Method", readonly = True )

    name = fields.Float('Quantity', digits=(16,2), readonly=True)
    product_qty_pending = fields.Float('Quantity Pending', digits=(16,2), readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    def __init__(self, pool, cr):
        drop_view_if_exists(cr, 'stock_product_by_location')
        cr.execute("""create or replace view stock_product_by_location
                   as
                   select min(id) as id ,location_id,product_id,
                   sum(name) as name, sum(product_qty_pending) as product_qty_pending, 
                   company_id
                   from stock_move_by_location
                   group by location_id,product_id,company_id
                   having round(sum(name),4) != 0 
                   ;""")

stock_product_by_location()

class stock_product_by_location_prodlot(models.Model):
    _name = "stock_product_by_location_prodlot"
    _description = "Product Stock Sum"
    _auto = False

    #'id'                 : fields.char    ('id',size=16, readonly=True),
    location_id = fields.Many2one('stock.location','Location', select=True, required=True, readonly=True)
    product_id = fields.Many2one('product.product','Product', select=True, required=True, readonly=True)
    categ_id = fields.Char(related='product_id.categ_id', string='Category', readonly=True)
    prodlot_id = fields.Many2one('stock.production.lot', 'Production lot', readonly=True, select=True)

    uom_id = fields.Char(related='product_id.uom_id', string="UoM", readonly = True )
    cost_method = fields.Char(related='product_id.cost_method', string="Cost Method", readonly = True )
    name = fields.Float('Quantity', digits=(16,2), readonly=True)
    product_qty_pending = fields.Float('Quantity Pending', digits=(16,2), readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    def __init__(self, pool, cr):
        drop_view_if_exists(cr, 'stock_product_by_location_prodlot')
        cr.execute("""create or replace view stock_product_by_location_prodlot
                   as
                   select min(id) as id ,location_id,product_id,prodlot_id,
                   sum(name) as name, sum(product_qty_pending) as product_qty_pending, 
                   company_id
                   from stock_move_by_location
                   group by location_id,prodlot_id,product_id,company_id
                   having round(sum(name),4) != 0
                   ;""")

stock_product_by_location_prodlot()

class product_product(models.Model):
    _inherit = "product.product"

    stock_product_by_location_ids = fields.One2many('stock_product_by_location','product_id','Product by Stock ')

    #copy must not copy stock_product_by_location_ids
    def copy (self, cr, uid, id, default={}, context=None):
        default = default.copy()
        default['stock_product_by_location_ids'] = []
        return super(product_product, self).copy (cr, uid, id, default, context)

product_product()

class stock_location(models.Model):
    _inherit = "stock.location"

    stock_product_by_location_ids = fields.One2many('stock_product_by_location','location_id','Product by Stock ')

    #copy must not copy stock_product_by_location_ids
    def copy (self, cr, uid, id, default={}, context=None):
        default = default.copy()
        default['stock_product_by_location_ids'] = []
        return super(stock_location, self).copy (cr, uid, id, default, context)

stock_location()


