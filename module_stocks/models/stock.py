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
        src_qty = None
        dest_qty = None
        wanted_qty = move.product_uom_qty

        if c_dst_id == 1: # dest is Beraud 
            # loc_rs : list of ids.
            src_qty = move.stock_qty_atom_dispo
            dst_qty = move.stock_qty_ber_dispo
            loc_src_rs = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DAT/Stock')])
            loc_dst_rs = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DC/Stock')])
        elif c_dst_id == 3:
            src_qty = move.stock_qty_ber_dispo
            dst_qty = move.stock_qty_atom_dispo
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

        # dst_qty : where we want the move to end up
        # src_qty : where we're taking the products from
        # src_qty can't be less than one (checked in function before)
        qty = 0
        if (src_qty + dst_qty) <= wanted_qty :
            qty = src_qty
        else:
            qty = wanted_qty - dst_qty

        move.availability = 10;
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
            'quantity': qty,
            'product_id':move.product_id.id, 
        }, context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.transfer.stock.intercompany',
            'name':u"Transfert de Stocks Inter-Sociétés",
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

            for move in pick.move_lines:
                move._compute_stock_nums()

                if move.stock_qty_atom_dispo == 0 and move.stock_qty_ber_dispo == 0:
                    print "both at zero, returning"
                    continue

                if move.stock_qty_atom_dispo + move.stock_qty_ber_dispo <= 0:
                    print "both stocks not enough to make more than zero, returning"
                    continue

                #if client belongs to Beraud, the product will be taken from beraud stock
                #so it needs to take from atom
                if pick.partner_id.company_id.id == 1: 
                    if move.stock_qty_ber_dispo < move.product_uom_qty:
                        if move.stock_qty_atom_dispo > 0:
                            #open tsis atom -> beraud
                            print "client belongs to Beraud but beraud stock too low and stocks from Atom disponible, opening tsis"
                            return self._open_tsis(cr, uid, ids, move, 3, 1, context)
                        elif move.stock_qty_ber_dispo == 0:
                            #if atom doesnt have anymore stock, and we have 0 quantity, do nothing
                            # call the normal function, that will also do nothing
                            print "doing nothing, nothing can be reserved. calling super"
                            res = super(StockPicking, self).action_assign(cr, uid, ids, context)
                        else:
                            #just reserve normally even if not enough
                            print "reserving normally, even if not enough. calling super"
                            res = super(StockPicking, self).action_assign(cr, uid, ids, context)
                    else:
                        print "client belongs to Beraud, stocks OK, not opening tsis"
                        res = super(StockPicking, self).action_assign(cr, uid, ids, context)

                #if client belongs to Atom, the product will be taken from atom stock
                #so it needs to take from beraud
                if pick.partner_id.company_id.id == 3: 
                    if move.stock_qty_atom_dispo < move.product_uom_qty:
                        if move.stock_qty_ber_dispo > 0:
                            #open tsis beraud -> atom
                            print "client belongs to Atom but atom stock too low and stocks from Beraud disponible, opening tsis"
                            return self._open_tsis(cr, uid, ids, move, 1, 3, context)
                        elif move.stock_qty_atom_dispo == 0:
                            #if beraud doesnt have anymore stock, and we have 0 quantity, do nothing
                            # call the normal function, that will also do nothing
                            print "doing nothing, nothing can be reserved, calling super"
                            res = super(StockPicking, self).action_assign(cr, uid, ids, context)
                        else:
                            #just reserve normally even if not enough
                            print "reserving normally, even if not enough. calling super"
                            res = super(StockPicking, self).action_assign(cr, uid, ids, context)
                    else:
                        print "client belongs to Atom, stocks OK, not opening tsis"
                        res = super(StockPicking, self).action_assign(cr, uid, ids, context)


        return res

import time

class StockMove(models.Model):
    _inherit = "stock.move"

    stock_qty_ber_dispo = fields.Float(compute='_compute_stock_nums', string=u"Quantité Disponible Stock Beraud")
    stock_qty_atom_dispo = fields.Float(compute='_compute_stock_nums', string=u"Quantité Disponible Stock Atom")

    stock_qty_ber_reserved = fields.Float(compute='_compute_stock_nums', string=u"Quantité Réservée Stock Beraud")
    stock_qty_atom_reserved = fields.Float(compute='_compute_stock_nums', string=u"Quantité Réservée Stock Atom")

    @api.multi
    def _compute_stock_nums(self):
        ''' function called to fill all four fields of the stock_move.
        computes the quantities in stock for a product, at two specific locations
        '''

        start = time.clock()
        print "in _compute_stock_nums"
        for move in self:

            print "product : %s" % move.product_id
            ber_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DC/Stock')])
            atom_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DAT/Stock')])

            #ber_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DC')])
            #atom_loc_rs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DAT')])

            ber_loc_ids = []
            for i in ber_loc_rs:
                ber_loc_ids.append(i.id)

            atom_loc_ids = []
            for i in atom_loc_rs:
                atom_loc_ids.append(i.id)

            #print "ber_loc_ids : ", ber_loc_ids
            #print "atom_loc_ids : ", atom_loc_ids
            #prods_in_ber = [x for x in sq_objs if x.product_id == move.product_id and x.location_id.id in ber_loc_ids]
            #prods_in_atom = [x for x in sq_objs if x.product_id == move.product_id and x.location_id.id in atom_loc_ids]

            print "[csn] move.product_id.name : ", move.product_id.name
            print "[csn] move.product_id.location_id : ", move.location_id
            print "[csn] move.product_id.location_dest_id : ", move.location_dest_id

            sq_ids_beraud = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id.id','in',ber_loc_ids)])
            sq_ids_atom = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id.id','in',atom_loc_ids)])

            # stock.quant(1,2,3...)
            print "sq_ids_beraud : ", sq_ids_beraud
            print "sq_ids_atom : ", sq_ids_atom

            qt = 0.0
            qr = 0.0
            move.stock_qty_ber_dispo = 0.0
            move.stock_qty_ber_reserved = 0.0
            for i in sq_ids_beraud:
                #print "name : %s " % self.env['product.product'].browse(i.product_id.id).name_template
                #print "location : %s " % self.env['stock.location'].browse(i.location_id.id).complete_name
                if i.reservation_id :
                    qr+=i.qty
                else:
                    qt+=i.qty

            move.stock_qty_ber_dispo = qt
            move.stock_qty_ber_reserved = qr
            #print "[csn]move.stock_qty_ber_dispo : ", move.stock_qty_ber_dispo
            #print "[csn]move.stock_qty_ber_reserved : ", move.stock_qty_ber_reserved

            qt = 0.0
            qr = 0.0
            move.stock_qty_atom_dispo = 0.0
            move.stock_qty_atom_reserved = 0.0
            for i in sq_ids_atom:
                #print "name : %s " % self.env['product.product'].browse(i.product_id.id).name_template
                #print "location : %s " % self.env['stock.location'].browse(i.location_id.id).complete_name
                #print "reservation_id : %s " % self.env['stock.move'].browse(i.reservation_id.id).name
                if i.reservation_id :
                    qr+=i.qty
                else:
                    qt+=i.qty

            move.stock_qty_atom_dispo = qt
            move.stock_qty_atom_reserved = qr
            #print "[csn]move.stock_qty_atom_dispo : ", move.stock_qty_atom_dispo
            #print "[csn]move.stock_qty_atom_reserved : ", move.stock_qty_atom_reserved

        print "time taken by _compute_stock_nums : %s" % (time.clock()-start)


class StockLocation(models.Model):
    _inherit = 'stock.location'

    tech = fields.Many2one('res.users', string="Technicien")

class StockQuants(models.Model):

    _inherit = 'stock.quant'

    def quants_get(self, cr, uid, qty, move, ops=False, domain=None, removal_strategy='fifo', context=None):
        """
        Use the removal strategies of product to search for the correct quants
        If you inherit, put the super at the end of your method.

        :location: browse record of the parent location where the quants have to be found
        :product: browse record of the product to find
        :qty in UoM of product
        """
        print ">>>>>>>>>>>>> our quants_get <<<<<<<<<<<<<<<<"
        domain = domain or [('qty', '>', 0.0)]
        domain = [d for d in domain if d[0] != 'company_id']
        print "dom temp : ", domain
        domain.append(('company_id', '=', move.location_id.company_id.id))
        print "new dom : ", domain
        # set company_id to move.location_id.company_id.
        return self.apply_removal_strategy(cr, uid, qty, move, ops=ops, domain=domain, removal_strategy=removal_strategy, context=context)


