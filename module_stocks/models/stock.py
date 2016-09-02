# -*- coding: utf-8 -*-

from openerp import models, api, fields

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
from utilsmod import utilsmod

from lxml import etree

import logging 
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    incoterm_id = fields.Many2one('stock.incoterms', 'Incoterms')

    create_date = fields.Datetime("Date")

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        mask = utilsmod.ReportMask(['module_stocks.report_my_picking', 'module_stocks.report_my_shipping2'])
        r = super(StockPicking, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(r, self)

    @api.v7
    def action_assign(self, cr, uid, ids, context=None):
        super(StockPicking, self).action_assign(cr, uid, ids, context)
        return True

class StockMove(models.Model):
    _inherit = "stock.move"

    stock_qty_ber = fields.Float(compute='_compute_stock_nums', string=u"Quantité Stock Beraud")
    stock_qty_atom = fields.Float(compute='_compute_stock_nums', string=u"Quantité Stock Atom")

    stock_qty_ber_reserved = fields.Float(compute='_compute_stock_nums', string=u"Quantité Réservée Stock Beraud")
    stock_qty_atom_reserved = fields.Float(compute='_compute_stock_nums', string=u"Quantité Réservée Stock Atom")

    @api.multi
    def _compute_stock_nums(self):
        for move in self:
            ls = ['stock_real','stock_virtual','stock_real_value','stock_virtual_value']

            ber_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/BER/Stock')])
            atom_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/ATOM/Stock')])

            ber_loc_ids = []
            for i in ber_loc_rs:
                ber_loc_ids.append(i.id)

            atom_loc_ids = []
            for i in atom_loc_rs:
                atom_loc_ids.append(i.id)

            # fetch all stock.quants
            sq_ids = self.env['stock.quant'].search([])
            sq_objs = []
            for i in sq_ids:
                sq_objs.append(self.env['stock.quant'].browse(i.id))

            prods_in_ber = [x for x in sq_objs if x.product_id == move.product_id and x.location_id.id in ber_loc_ids]
            prods_in_atom = [x for x in sq_objs if x.product_id == move.product_id and x.location_id.id in atom_loc_ids]

            #print "**** for product : %s" % self.env['product.product'].browse(move.product_id.id).name_template
            #print "***in beraud stock"
            qt = 0
            qr = 0
            for i in prods_in_ber:
                #print "name : %s " % self.env['product.product'].browse(i.product_id.id).name_template
                #print "location : %s " % self.env['stock.location'].browse(i.location_id.id).complete_name
                #print "quantity : %s " % i.qty
                #print "reservation_id : %s " % self.env['stock.move'].browse(i.reservation_id.id).name
                qt+=i.qty
                if i.reservation_id :
                    qr+=i.qty

            #print "quantity in stock : %s" % qt
            #print "quantity reserved : %s" % qr
            move.stock_qty_ber = qt
            move.stock_qty_ber_reserved = qr

            #print "***in atom stock"
            qt = 0
            qr = 0
            for i in prods_in_atom:
                #print "name : %s " % self.env['product.product'].browse(i.product_id.id).name_template
                #print "location : %s " % self.env['stock.location'].browse(i.location_id.id).complete_name
                #print "quantity : %s " % i.qty
                #print "reservation_id : %s " % self.env['stock.move'].browse(i.reservation_id.id).name
                qt+=i.qty
                if i.reservation_id :
                    qr+=i.qty

            #print "quantity in stock : %s" % qt
            #print "quantity reserved : %s" % qr
            move.stock_qty_atom = qt
            move.stock_qty_atom_reserved = qr


