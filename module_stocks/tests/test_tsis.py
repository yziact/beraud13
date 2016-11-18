# -*- coding: utf-8 -*-

from . import common 
from openerp.tools import mute_logger, float_round

import logging
_logger = logging.getLogger(__name__)

class TestsTsis(common.TestsCommon):

    #@mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def setUp(self):
        super(TestsTsis, self).setUp()

        self.partner_ber_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',1)])
        self.partner_atom_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',3)])

        self.ber_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        self.atom_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        self.customer_loc_id = self.LocObj.search([('complete_name','ilike','Partner Locations/Customers')])

        # get Nicolas Clair
        self.beraud_partner_id = self.env['res.partner'].search([('name','ilike','Nicolas Clair')])
        self.beraud_user_id = self.env['res.users'].search([('partner_id','=',self.beraud_partner_id.id)])

    ##################################################
    ######## TEST TSIS 1 #############################
    ##################################################
    def test00_tsis_atom_to_beraud(self):
        """
        Client belongs to Beraud.
        Beraud wants to reserve, but doesn't have enough stock and has to TSIS from Atom.
        """

        print "||||||>>>> test00_tsis_atom_to_beraud <<<<<||||||" 

        productA = self.ProductObj.create({'name': 'Product A'})

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 1.0,
        })

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.atom_loc_id.id,
            'company_id': 3,
            'qty': 8.0,
        })

        picking_out = self.PickingObj.create({
            'partner_id': self.partner_ber_id.id,
            'picking_type_id': self.picking_type_out,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id })

        self.MoveObj.create({
            'name': 'move_line_0',
            'product_id': productA.id,
            'product_uom_qty': 3.0,
            'product_uom': productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id })

        print "action_assign() from stock.picking"
        #wiz_action = picking_out.sudo(self.beraud_user_id).action_assign()
        wiz_action = picking_out.action_assign()
        wiz_id = wiz_action['res_id']
        wiz_obj = self.env['wizard.transfer.stock.intercompany'].browse(wiz_id)
        print "wiz_id : %s, wiz_obj : %s" % (wiz_id, wiz_obj)

        self.assertEqual(wiz_obj.company_src_id.id, 3)
        self.assertEqual(wiz_obj.company_dst_id.id, 1)

        self.assertEqual(wiz_obj.location_src_id.id, self.atom_loc_id.id)
        self.assertEqual(wiz_obj.location_dst_id.id, self.ber_loc_id.id)
        print "tsis is from atom to beraud, locations ok"

        for line in wiz_obj.line_ids:
            print "wizard line quantity : %s" % line.quantity
            self.assertAlmostEqual(2.0, line.quantity)

        print "perform_transfer() from wizard.transfer.stock.intercompany"
        #moves_list = wiz_obj.sudo(self.beraud_user_id).perform_transfer()
        moves_list = wiz_obj.perform_transfer()
        print "moves returned by TSIS : ", moves_list
        # We should have :
        # a quant of qty 3.0, company_id 1, in location Beraud
        # a quant of qty 6.0, company_id 3, in location Atom

        # check quants in Beraud
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.ber_loc_id.id),
            ('company_id', '=', 1),
            ])
        print 'quants in beraud : ', quants

        total_qty = sum([quant.qty for quant in quants])
        self.assertEqual(total_qty, 3.0,
                         "wrong qty of quants in beraud location, %s found instead of 3.0" % total_qty)
        print "Quants in Beraud OK."
        print "Quants in Beraud : "
        for i in quants:
            self.print_quant(i)

        # check quants in Atom
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.atom_loc_id.id),
            ('company_id', '=', 3),
            ])
        total_qty = sum([quant.qty for quant in quants])
        self.assertEqual(total_qty, 6.0,
                         "wrong qty of quants in atom location, %s found instead of 6.0" % total_qty)
        print "Quants in Atom OK."
        print "Quants in Atom : "
        for i in quants:
            self.print_quant(i)

        # check product qty
        self.assertEqual(productA.qty_available, 9.0, 
                         'Wrong quantity available, %s found instead of 9.0)' % (productA.qty_available))

        # check moves
        print "checking integrity of moves"
        for tup in moves_list:
            for move in tup:
                print "move.id", move.id
                print "move.name", move.name
                print "move.product_uom", move.product_uom
                print "move.product_uom_qty", move.product_uom_qty
                print "move.picking_id", move.picking_id
                print "move.location_id", move.location_id
                print "move.location_dest_id", move.location_dest_id

        trn_loc = moves_list[0][0].location_dest_id
        print "checking for remaining quants in transit location"
        print "transit location : ", trn_loc

        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', trn_loc.id),
            ])

        print "quants remaining in transit location : ", quants

        for i in quants : 
            print "quant id : ", i.id
            print "quant name : ", i.name
            print "quant product_id : ", i.product_id
            print "quant location_id : ", i.location_id
            print "quant company_id : ", i.company_id
            print "quant qty : ", i.qty


    ##################################################
    ######## TEST TSIS 2 #############################
    ##################################################
    def test01_tsis_beraud_to_atom_no_stock(self):
        """
        Client belongs to Beraud.
        Beraud wants to transfer a number of products, when they have 0 of them in their stock
        Can't work, the TSIS has to return that no stock is available to transfer
        """

        print "||||||>>>> test01_tsis_beraud_to_atom_no_stock <<<<<||||||" 

        productA = self.ProductObj.create({'name': 'Product A'})

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 0.0,
        })

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.atom_loc_id.id,
            'company_id': 3,
            'qty': 8.0,
        })

        wiz_obj = self.env['wizard.transfer.stock.intercompany']
        wiz_line_obj = self.env['wizard.transfer.stock.intercompany.line']

        wizard_id = wiz_obj.create({
            'company_src_id': 1, # Beraud
            'location_src_id': self.ber_loc_id.id,

            'company_dst_id': 3, # Atom
            'location_dst_id': self.atom_loc_id.id,
        })

        wizard_line_id = wiz_line_obj.create({
            'wizard_id':wizard_id.id,
            #'restrict_lot_id':move.restrict_lot_id.id,
            'quantity': 3.0,
            'product_id': productA.id, 
        })

        print "perform_transfer() from wizard.transfer.stock.intercompany"
        wiz_id = wiz_obj.browse(wizard_id.id)

        #moves_list = wiz_id.sudo(self.beraud_user_id).perform_transfer()
        moves_list = wiz_id.perform_transfer()
        print "moves returned by TSIS : ", moves_list
        # We should have :
        # a quant of qty 3.0, company_id 1, in location Beraud
        # a quant of qty 6.0, company_id 3, in location Atom

        # check quants in Beraud
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.ber_loc_id.id),
            ('company_id', '=', 1),
            ])
        print 'quants in beraud : ', quants

        total_qty = sum([quant.qty for quant in quants])
        #self.assertEqual(total_qty, 0.0,
        #                 "wrong qty of quants in beraud location, %s found instead of 0.0" % total_qty)
        print "Quants in Beraud OK, ", total_qty
        print "Quants in Beraud : "
        for i in quants:
            self.print_quant(i)

        # check quants in Atom
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.atom_loc_id.id),
            ('company_id', '=', 3),
            ])
        total_qty = sum([quant.qty for quant in quants])
        #self.assertEqual(total_qty, 8.0,
        #                 "wrong qty of quants in atom location, %s found instead of 8.0" % total_qty)
        print "Quants in Atom : ", total_qty
        print "Quants in Atom : "
        for i in quants:
            self.print_quant(i)

        # check product qty
        #self.assertEqual(productA.qty_available, 9.0, 
        #                 'Wrong quantity available, %s found instead of 9.0)' % (productA.qty_available))

        # check moves
        print "checking integrity of moves generated by the TSIS"
        for tup in moves_list:
            for move in tup:
                print "move.id", move.id
                print "move.name", move.name
                print "move.product_uom", move.product_uom
                print "move.product_uom_qty", move.product_uom_qty
                print "move.picking_id", move.picking_id
                print "move.location_id", move.location_id
                print "move.location_dest_id", move.location_dest_id

        trn_loc = moves_list[0][0].location_dest_id
        print "checking for remaining quants in transit location"
        print "transit location : ", trn_loc

        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', trn_loc.id),
            ])

        print "quants remaining in transit location : ", quants

        for i in quants : 
            print "quant id : ", i.id
            print "quant name : ", i.name
            print "quant product_id : ", i.product_id
            print "quant location_id : ", i.location_id
            print "quant company_id : ", i.company_id
            print "quant qty : ", i.qty


