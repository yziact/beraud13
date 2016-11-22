# -*- coding: utf-8 -*-

from openerp import models, api, fields

from openerp.exceptions import UserError

from lxml import etree

import logging 
_logger = logging.getLogger(__name__)

class OurStockPicking(models.Model):
    _inherit = 'stock.picking'

    """
    def do_new_transfer(self, cr, uid, ids, context=None):
        print "[%s] do_new_transfer" % (__name__)
        return super(OurStockPicking, self).do_new_transfer(cr, uid, ids, context)
    """

    # set saled_id.last_picking_id
    def do_transfer(self, cr, uid, ids, context=None):

        print "[%s] do_transfer" % (__name__)

        for picking in self.browse(cr, uid, ids, context=context):
            if not picking.sale_id :
                continue

            print "setting sale_id.last_picking_id to our id (we're the last validated one)"
            print "picking.sale_id : ", picking.sale_id
            print "picking : ", picking
            picking.sale_id.last_picking_id = picking

        return super(OurStockPicking, self).do_transfer(cr, uid, ids, context)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # field updated by the stock.picking when it gets validated
    last_picking_id = fields.Many2one('stock.picking',
                                      string='Last validated Delivery Order',
                                      store=True)

    last_picking_id_date_done = fields.Datetime(related='last_picking_id.date_done',
                                                string='Date of Last Delivery Order',
                                                store=True)

