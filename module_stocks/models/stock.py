# -*- coding: utf-8 -*-

from openerp import models, api, fields

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
from utilsmod import utilsmod

from openerp.exceptions import UserError

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

    def _open_tsis(self, cr, uid, ids, move, c_src_id, c_dst_id, context=None):

        loc_obj = self.pool.get('stock.location')

        loc_src_rs = None
        loc_dst_rs = None
        if c_dst_id == 1: 
            # loc_rs : list of ids.
            loc_src_rs = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DAT/Stock')])
            loc_dst_rs = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DC/Stock')])
        elif c_dst_id == 3:
            loc_src_rs = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DC/Stock')])
            loc_dst_rs = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DAT/Stock')])
        else:
            raise UserError("Wrong Company ID was passed to _open_tsis.")
        print "loc_src_rs : %s" % loc_src_rs
        print "loc_dst_rs : %s" % loc_dst_rs

        loc_src_obj = loc_obj.browse(cr, uid, loc_src_rs[0])
        loc_dst_obj = loc_obj.browse(cr, uid, loc_dst_rs[0])
        print "loc_src_obj : %s" % loc_src_obj
        print "loc_dst_obj : %s" % loc_dst_obj

        if (not loc_src_obj) or (not loc_dst_obj) :
            raise UserError("Something went wrong while getting the source/destination location of the tsis")
        
        wizard_id = self.pool.get('wizard.transfer.stock.intercompany').create(cr, uid, {
            'company_src_id':c_src_id, # Beraud
            #'location_src_id':move.product_id.location_id.id, # is NULL...
            #'location_src_id':move.location_id.id,
            'location_src_id':loc_src_obj.id,
            'company_dst_id':c_dst_id, # Atom
            #'location_dst_id':move.location_dest_id.id,
            'location_dst_id':loc_dst_obj.id,
        }, context)
        wizard_line_id = self.pool.get('wizard.transfer.stock.intercompany.line').create(cr, uid, {
            'wizard_id':wizard_id,
            'restrict_lot_id':move.restrict_lot_id.id,
            'quantity': (move.product_uom_qty if move.stock_qty_ber >= move.product_uom_qty else
                        move.stock_qty_ber),
            'product_id':move.product_id.id, 
        }, context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.transfer.stock.intercompany',
            'name':"Transfert de Stocks Inter-Sociétés",
            'view_mode': 'form',
            #'view_id': False,
            #'nodestroy': True,
            'view_type': 'form',
            'res_id': wizard_id,
            'target': 'new',
            'context': context
        }

    #@api.v7
    def action_assign(self, cr, uid, ids, context=None):

        move_obj = self.pool.get('stock.move')
        loc_obj = self.pool.get('stock.location')

        print "our action assign"
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):

            # if client belongs to ATOM
            if pick.partner_id.company_id.id == 3: 
                for move in pick.move_lines:
                    #print "move.product_uom_qty : %s" % move.product_uom_qty
                    if move.stock_qty_atom < move.product_uom_qty:
                        #then open TSIS Beraud -> Atom
                        print "client belongs to Atom but atom stock too low, opening tsis"
                        return self._open_tsis(cr, uid, ids, move, 1, 3, context)
                    else:
                        print "client belongs to Atom, stocks OK, not opening tsis"
                        res = super(StockPicking, self).action_assign(cr, uid, ids, context)

            # if client belongs to BERAUD
            elif pick.partner_id.company_id.id == 1:
                for move in pick.move_lines:
                    #print "move.product_uom_qty : %s" % move.product_uom_qty
                    if move.stock_qty_ber < move.product_uom_qty:
                        #then open TSIS Atom -> Beraud
                        return self._open_tsis(cr, uid, ids, move, 3, 1, context)
                        print "client belongs to Beraud but beraud stock too low, opening tsis"
                    else:
                        print "client belongs to Beraud, stocks OK, not opening tsis"
                        res = super(StockPicking, self).action_assign(cr, uid, ids, context)

        return res

class StockMove(models.Model):
    _inherit = "stock.move"

    stock_qty_ber = fields.Float(compute='_compute_stock_nums', string=u"Quantité Stock Beraud")
    stock_qty_atom = fields.Float(compute='_compute_stock_nums', string=u"Quantité Stock Atom")

    stock_qty_ber_reserved = fields.Float(compute='_compute_stock_nums', string=u"Quantité Réservée Stock Beraud")
    stock_qty_atom_reserved = fields.Float(compute='_compute_stock_nums', string=u"Quantité Réservée Stock Atom")

    @api.multi
    def _compute_stock_nums(self):
        for move in self:

            ber_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DC')])
            atom_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DAT')])

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


class StockLocation(models.Model):
    _inherit = "stock.location"

    tech = fields.Many2one('res.users', string="Technicien")

