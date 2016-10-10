# -*- coding: utf-8 -*-

from . import common 
from openerp.tools import mute_logger, float_round

import logging
_logger = logging.getLogger(__name__)

class TestStockPicking(common.TestsCommon):

    #@mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def setUp(self):
        super(TestStockPicking, self).setUp()

        self.partner_ber_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',1)])
        self.partner_atom_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',3)])

        self.ber_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        self.atom_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        self.customer_loc_id = self.LocObj.search([('complete_name','ilike','Partner Locations/Customers')])

        # get Nicolas Clair
        self.beraud_partner_id = self.env['res.partner'].search([('name','ilike','Nicolas Clair')])
        self.beraud_user_id = self.env['res.users'].search([('partner_id','=',self.beraud_partner_id.id)])

    ### basic reservation ###
    def test04_reserve_beraud(self):
        print "test00_reserve_beraud" 

        # create product and quants for product
        productA = self.ProductObj.create({'name': 'Product A'})

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.atom_loc_id.id,
            'company_id': 3,
            'qty': 0.0,
        })

        #print "CUSTOMER LOC ID : %s ", self.customer_loc_id
        #print "BER LOC ID : %s ",  self.ber_loc_id
        #print "ATOM LOC ID : %s ",  self.atom_loc_id
        #print "PARTNER ID : %s ", self.partner_ber_id

        picking_out = self.PickingObj.create({
            'partner_id': self.partner_ber_id.id,
            'picking_type_id': self.picking_type_out,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
        })

        move_line_0 = self.MoveObj.create({
            'name': 'move_line_0',
            'product_id': productA.id,
            'product_uom_qty': 3.0,
            'product_uom': productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
        })

        #self.picking_out.sudo(self.user_beraud).action_assign()
        picking_out.action_assign()
        self.assertAlmostEqual(7.0, productA.virtual_available)
        print "self.productA.virtual_available : ", productA.virtual_available
        print "OK"

    def test05_reserve_atom(self):
        print "test01_reserve_atom" 

        # create product and quants for product
        productA = self.ProductObj.create({'name': 'Product A'})

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 6.0,
        })

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.atom_loc_id.id,
            'company_id': 3,
            'qty': 10.0,
        })

        #print "CUSTOMER LOC ID : %s ", self.customer_loc_id
        #print "BER LOC ID : %s ",  self.ber_loc_id
        #print "ATOM LOC ID : %s ",  self.atom_loc_id
        #print "PARTNER ID : %s ", self.partner_ber_id

        picking_out = self.PickingObj.create({
            'partner_id': self.partner_ber_id.id,
            'picking_type_id': self.picking_type_out,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
        })

        move_line_0 = self.MoveObj.create({
            'name': 'move_line_0',
            'product_id': productA.id,
            'product_uom_qty': 3.0,
            'product_uom': productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
        })

        #self.picking_out.sudo(self.user_beraud).action_assign()
        picking_out.action_assign()
        self.assertAlmostEqual(13.0, productA.virtual_available)
        print "self.productA.virtual_available : ", productA.virtual_available
        print "OK, 13."

    """
    def test_reserve_with_tsis(self):
        print "test_stock_picking_reserve_with_tsis" 
        # create product and quants for product
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
            'qty': 2.0,
        })

        #print "CUSTOMER LOC ID : %s ", self.customer_loc_id
        #print "BER LOC ID : %s ",  self.ber_loc_id
        #print "ATOM LOC ID : %s ",  self.atom_loc_id
        #print "PARTNER ID : %s ", self.partner_ber_id

        picking_out = self.PickingObj.create({
            'partner_id': self.partner_ber_id.id,
            'picking_type_id': self.picking_type_out,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
        })

        move_line_0 = self.MoveObj.create({
            'name': 'move_line_0',
            'product_id': productA.id,
            'product_uom_qty': 3.0,
            'product_uom': productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
        })

        #self.picking_out.sudo(self.user_beraud).action_assign()
        print "*** --> action_assign on picking_out as beraud user"
        #picking_out.sudo(self.beraud_user_id).action_assign()
    """

    def test00_tsis_atom_to_beraud(self):
        """
        Client belongs to Beraud.
        Beraud wants to reserve, but doesn't have enough stock and has to TSIS from Atom.
        """

        print "||||||>>>> test00_tsis_atom_beraud <<<<<||||||" 

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
        #res = picking_out.sudo(self.beraud_user_id).action_assign()
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
            print "quantity ok"

        print "perform_transfer() from wizard.transfer.stock.intercompany"
        moves_list = wiz_obj.perform_transfer()
        # We should have :
        # a quant of qty 1.0, company_id 1, in location Beraud
        # a quant of qty 2.0, company_id 1, in location Beraud
        # a quant of qty 6.0, company_id 3, in location Atom
        # check quants in Beraud
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.ber_loc_id.id),
            ('company_id', '=', 1),
            ])
        total_qty = sum([quant.qty for quant in quants])
        self.assertEqual(total_qty, 3.0,
                         "wrong qty of quants in beraud location, %s found instead of 3.0" % total_qty)
        self.assertEqual(productA.qty_available, 9.0, 
                         'Wrong quantity available, %s found instead of 9.0)' % (productA.qty_available))
        print "Quants in Beraud OK."

        # check quants in Atom
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.atom_loc_id.id),
            ('company_id', '=', 3),
            ])
        total_qty = sum([quant.qty for quant in quants])
        self.assertEqual(total_qty, 6.0,
                         "wrong qty of quants in atom location, %s found instead of 3.0" % total_qty)
        self.assertEqual(productA.qty_available, 9.0, 
                         'Wrong quantity available, %s found instead of 9.0)' % (productA.qty_available))
        print "Quants in Atom OK."

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

    def test01_tsis_beraud_to_atom(self):
        """
        Client belongs to Atom.
        Atom wants to reserve, but doesn't have enough stock and has to TSIS from Beraud.
        Mirror of previous unit test.
        Beraud has 12, Atom has 5, Atom wants to reserve 7.
        """

        print "||||||>>>> test01_tsis_beraud_to_atom <<<<<||||||" 

        productA = self.ProductObj.create({'name': 'Product A'})

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 12.0,
        })

        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.atom_loc_id.id,
            'company_id': 3,
            'qty': 5.0,
        })

        picking_out = self.PickingObj.create({
            'partner_id': self.partner_atom_id.id, # partner belongs to atom
            'picking_type_id': self.picking_type_out,
            'location_id': self.atom_loc_id.id, # from location atom
            'location_dest_id': self.customer_loc_id.id })

        self.MoveObj.create({
            'name': 'move_line_0',
            'product_id': productA.id,
            'product_uom_qty': 7.0,
            'product_uom': productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.atom_loc_id.id, # from location atom
            'location_dest_id': self.customer_loc_id.id })

        print "action_assign() from stock.picking"
        #res = picking_out.sudo(self.beraud_user_id).action_assign()
        wiz_action = picking_out.action_assign()
        wiz_id = wiz_action['res_id']
        wiz_obj = self.env['wizard.transfer.stock.intercompany'].browse(wiz_id)
        print "wiz_id : %s, wiz_obj : %s" % (wiz_id, wiz_obj)

        self.assertEqual(wiz_obj.company_src_id.id, 1)
        self.assertEqual(wiz_obj.company_dst_id.id, 3)

        self.assertEqual(wiz_obj.location_src_id.id, self.ber_loc_id.id)
        self.assertEqual(wiz_obj.location_dst_id.id, self.atom_loc_id.id)
        print "tsis is from beraud to atom, locations ok"

        for line in wiz_obj.line_ids:
            print "wizard line quantity : %s" % line.quantity
            self.assertAlmostEqual(2.0, line.quantity)
            print "quantity ok"

        print "perform_transfer() from wizard.transfer.stock.intercompany"
        moves_list = wiz_obj.perform_transfer()
        # We should have :
        # a quant of qty 10.0, company_id 1, in location Beraud
        # a quant of qty 5.0, company_id 3, in location Atom
        # a quant of qty 2.0, company_id 3, in location Atom
        # check quants in Beraud
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.ber_loc_id.id),
            ('company_id', '=', 1),
            ])
        total_qty = sum([quant.qty for quant in quants])
        self.assertEqual(total_qty, 10.0,
                        "wrong qty of quants in beraud location, %s found instead of 10.0" % total_qty)
        self.assertEqual(productA.qty_available, 17.0, 
                        'Wrong quantity available, %s found instead of 17.0)' % (productA.qty_available))
        print "Quants in Beraud OK."

        # check quants in Atom
        quants = self.env['stock.quant'].search([
            ('product_id', '=', productA.id),
            ('location_id', '=', self.atom_loc_id.id),
            ('company_id', '=', 3),
            ])
        total_qty = sum([quant.qty for quant in quants])
        self.assertEqual(total_qty, 7.0,
                        "wrong qty of quants in atom location, %s found instead of 7.0" % total_qty)
        self.assertEqual(productA.qty_available, 17.0, 
                        'Wrong quantity available, %s found instead of 17.0)' % (productA.qty_available))
        print "Quants in Atom OK."

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

        print "assigning stock now that TSIS is done."
        picking_out.action_assign()

        '''    
        quant_objs = self.env['stock.quant'].browse(quant_ids)        
        print "quant objs : ", quant_objs
        '''

        '''
        wiz_id = self.env['wizard.transfer.stock.intercompany'].create({
            'company_src_id':1, # Beraud
            'location_src_id':self.ber_loc_id.id,
            'company_dst_id':3, # Atom
            'location_dst_id':self.atom_loc_id.id })

        wizard_line_id = self.env['wizard.transfer.stock.intercompany.line'].create({
            'wizard_id': wiz_id.id,
            #'restrict_lot_id': 'none', # comes from the move that spawns the wizard
            'quantity': 10, 
            'product_id': productA.id })
        '''

    """
    def test_stock_on_hand_updates_atom(self):
        print "|||||| test_stock_on_hand_updates_atom ||||||" 

        # create product and quants for product
        productA = self.ProductObj.create({'name': 'Product A'})

        q1 = self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 4.0,
        })
        print "created quant for product_A, loc beraud, company_id = 1, qty = 4.0. id : ", q1

        q2 = self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.atom_loc_id.id,
            'company_id': 3,
            'qty': 7.0,
        })
        print "created quant for product_A, loc atom, company_id = 3, qty = 7.0. id : ", q2

        wiz_id = self.env['stock.change.product.qty'].create({
            'product_id':productA.id, 
        })
        #wiz_id.product_id = productA.id

        wiz_id.location_id = self.atom_loc_id
        wiz_id.new_quantity = 10
        wiz_id.change_product_qty()

        print 'productA.qty_available : ', productA.qty_available
        print 'productA.virtual_available : ', productA.virtual_available
        print 'productA.incoming_qty : ', productA.incoming_qty
        print 'productA.outgoing_qty : ', productA.outgoing_qty

        self.assertAlmostEqual(14.0, productA.virtual_available)
    """

    """
    def test_stock_on_hand_updates_beraud(self):
        print "|||||| test_stock_on_hand_updates_beraud ||||||" 

        #print "GROUPS ARE : "
        #print "THESE : ", self.env['res.groups'].search([])

        # create product and quants for product
        productA = self.ProductObj.create({'name': 'Product A'})

        q1 = self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 3.0,
        })
        print "created quant for product_A, loc beraud, company_id = 1, qty = 3.0. id : ", q1

        q2 = self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.atom_loc_id.id,
            'company_id': 3,
            'qty': 5.0,
        })
        print "created quant for product_A, loc atom, company_id = 3, qty = 5.0. id : ", q2
        wiz_id = self.env['stock.change.product.qty'].create({
            'product_id':productA.id, 
        })
        #wiz_id.product_id = productA.id

        wiz_id.location_id = self.ber_loc_id
        wiz_id.new_quantity = 10
        wiz_id.change_product_qty()

        #print 'productA.qty_available : ', productA.qty_available
        #print 'productA.virtual_available : ', productA.virtual_available
        #print 'productA.incoming_qty : ', productA.incoming_qty
        #print 'productA.outgoing_qty : ', productA.outgoing_qty

        self.assertAlmostEqual(15.0, productA.virtual_available)
    """


