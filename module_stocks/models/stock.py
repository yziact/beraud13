# -*- coding: utf-8 -*-

from openerp import models, api, fields

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
sys.path.insert(0, '/mnt/extra-addons/')
from utilsmod import utilsmod

from openerp.exceptions import UserError

from lxml import etree

import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    repair_id = fields.Many2one('mrp.repair', 'Reparation')
    incoterm_id = fields.Many2one('stock.incoterms', 'Incoterms')
    create_date = fields.Datetime("Date")
    reliquat = fields.Boolean("Reliquat")

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):

        mask = utilsmod.ReportMask(['module_stocks.report_my_picking'])
        r = super(StockPicking, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(r, self)

    def _open_tsis(self, cr, uid, ids, c_src_id, c_dst_id, moves, context=None):

        loc_obj = self.pool.get('stock.location')

        loc_src_id = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DAT/Stock')])
        loc_dst_id = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DC/Stock')])
        print "loc_src_id : ", loc_src_id
        print "loc_dst_id : ", loc_dst_id

        if c_dst_id == 3: # dest is Beraud
            loc_src_id = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DC/Stock')])
            loc_dst_id = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DAT/Stock')])

        loc_src_obj = loc_obj.browse(cr, uid, loc_src_id)
        loc_dst_obj = loc_obj.browse(cr, uid, loc_dst_id)

        wizard_id = self.pool.get('wizard.transfer.stock.intercompany').create(cr, uid, {
            'company_src_id':c_src_id, # Beraud
            #'location_src_id':move.product_id.location_id.id, # is NULL...
            #'location_src_id':move.location_id.id,
            'location_src_id':loc_src_obj.id,
            'company_dst_id':c_dst_id, # Atom
            #'location_dst_id':move.location_dest_id.id,
            'location_dst_id':loc_dst_obj.id,
        }, context)

        print "wizard_id : ", wizard_id
        print "moves : ", moves

        for move in moves:

            wanted_qty = move.product_uom_qty

            src_qty = move.stock_qty_atom_dispo
            dst_qty = move.stock_qty_ber_dispo

            if c_dst_id == 3:
                src_qty = move.stock_qty_ber_dispo
                dst_qty = move.stock_qty_atom_dispo

            qty = 0
            if (src_qty + dst_qty) <= wanted_qty :
                qty = src_qty
            else:
                qty = wanted_qty - dst_qty

            if move.origin and 'OR' in move.origin:
                origin = move.origin
            else:
                origin = move.picking_id.name

            wizard_line_id = self.pool.get('wizard.transfer.stock.intercompany.line').create(cr, uid, {
                'wizard_id':wizard_id,
                'restrict_lot_id': move.restrict_lot_id.id,
                'quantity': qty,
                'product_id': move.product_id.id,
                'origin': origin,
                'date': move.date,
            }, context)

        print "returning"
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

    def check_stocks_for_move(self, pick, move, src_comp, dst_comp):

        #if client belongs to Beraud, the product will be taken from beraud stock
        #so it needs to take from atom
        moves = []
        comp_rels = {1:'BERAUD', 3:'ATOM'}

        stock_qty_dispo = move.stock_qty_ber_dispo
        stock_qty_other_dispo = move.stock_qty_atom_dispo

        if src_comp == 3:
            stock_qty_dispo = move.stock_qty_atom_dispo
            stock_qty_other_dispo = move.stock_qty_ber_dispo

        if stock_qty_dispo == 0 and stock_qty_other_dispo == 0:
            print "both at zero, returning"
            return

        if stock_qty_dispo + stock_qty_other_dispo <= 0:
            print "both stocks not enough to make more than zero, returning"
            return

        if stock_qty_dispo < move.product_uom_qty:
            if stock_qty_other_dispo > 0:
                #open tsis src -> dest
                print "client belongs to %s but their stock is too low and stocks from %s disponible, opening tsis" % (comp_rels[src_comp], comp_rels[dst_comp])
                return move
            elif stock_qty_other_dispo == 0:
                #if other company doesnt have anymore stock, and we have 0 quantity, do nothing
                # call the normal function, that will also do nothing
                print "We (%s) don't have anymore stock, and the other company doesn't neither." % comp_rels[src_comp]
            else:
                #just reserve normally even if not enough
                print "reserving normally for %s , even if not enough." % comp_rels[src_comp]
        else:
            print "client belongs to %s, stocks OK, not opening tsis" % comp_rels[src_comp]

        return


    def action_assign(self, cr, uid, ids, context=None):

        move_obj = self.pool.get('stock.move')
        loc_obj = self.pool.get('stock.location')

        print "[module_stock action_assign] our action assign"

        for pick in self.browse(cr, uid, ids, context=context):

            #print "pick.picking_type_id.name : ", pick.picking_type_id.name
            # if the picking is a reception, we don't do anything
            print(pick.picking_type_id.name)

            if u'Réceptions'in pick.picking_type_id.name  or u'Receipts' in pick.picking_type_id.name:
                print "[action_assign] reception, calling super"
                super(StockPicking, self).action_assign(cr, uid, pick.id, context)
                continue

            if 'SAV' in pick.picking_type_id.name :
                print "[action_assign] SAV, calling super"
                super(StockPicking, self).action_assign(cr, uid, pick.id, context)
                continue

            if pick.location_id.tech :
                super(StockPicking, self).action_assign(cr, uid, pick.id, context)
                continue

            if pick.reliquat:
                super(StockPicking, self).action_assign(cr, uid, pick.id, context)
                continue

            r = []
            src = 1
            dst = 3
            #print "[module_stock action_assign] pick.partner_id : ", pick.partner_id
            #print "[module_stock action_assign] pick.partner_id.company_id.id : ", pick.partner_id.company_id.id
            if not pick.partner_id:
                if pick.location_dest_id.company_id.id == 3:
                    src = 3
                    dst = 1
            elif pick.partner_id.company_id.id == 3 :
                src = 3
                dst = 1

            for move in pick.move_lines:
                move._compute_stock_nums()
                # src is our company, dst is the other
                m = self.check_stocks_for_move(pick, move, src, dst)
                if m :
                    r.append(m)
            if r :
                print "opening tsis"
                return self._open_tsis(cr, uid, ids, dst, src, r)
            else :
                print "calling super.action_assign()"
                #super(StockPicking, pick).action_assign(cr, uid, ids, context=context)
                super(StockPicking, self).action_assign(cr, uid, pick.id, context)
                move._compute_stock_nums()

        return {}

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
            #ber_loc_recs = self.env['stock.location'].search(['|', ('complete_name','ilike','Physical Locations/DC/Stock'),
            #                                                 ('complete_name','ilike','Emplacements Physiques/DC/REP')
            #                                                ])
            #atom_loc_recs = self.env['stock.location'].search(['|', ('complete_name','ilike','Physical Locations/DAT/Stock'),
            #                                                 ('complete_name','ilike','Emplacements Physiques/DAT/REP')
            #                                                ])
            ber_loc_recs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DC/Stock')])
            atom_loc_recs = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DAT/Stock')])

            print "ber_loc_recs : ", ber_loc_recs
            print "ber_loc_recs.ids : ", ber_loc_recs.ids
            print "atom_loc_recs : ", atom_loc_recs
            print "atom_loc_recs.ids : ", atom_loc_recs.ids
            ber_loc_ids = ber_loc_recs.ids
            atom_loc_ids = atom_loc_recs.ids

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
        #print ">>>>>>>>>>>>> our quants_get <<<<<<<<<<<<<<<<"
        domain = domain or [('qty', '>', 0.0)]
        domain = [d for d in domain if d[0] != 'company_id']
        if move.location_id.company_id.id :
            domain.append(('company_id', '=', move.location_id.company_id.id))
        print "[our_quants_get] new domain : ", domain
        # set company_id to move.location_id.company_id.
        return self.apply_removal_strategy(cr, uid, qty, move, ops=ops, domain=domain, removal_strategy=removal_strategy, context=context)


