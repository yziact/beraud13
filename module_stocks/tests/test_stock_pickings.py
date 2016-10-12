# -*- coding: utf-8 -*-

from . import common 
from openerp.tools import mute_logger, float_round

import logging
_logger = logging.getLogger(__name__)

class TestsStockPicking(common.TestsCommon):

    #@mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def setUp(self):
        super(TestsStockPicking, self).setUp()

        self.partner_ber_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',1)])
        self.partner_atom_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',3)])

        self.ber_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        self.atom_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        self.customer_loc_id = self.LocObj.search([('complete_name','ilike','Partner Locations/Customers')])

        # get Nicolas Clair
        self.beraud_partner_id = self.env['res.partner'].search([('name','ilike','Nicolas Clair')])
        self.beraud_user_id = self.env['res.users'].search([('partner_id','=',self.beraud_partner_id.id)])

    ### basic reservation ###
    """
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
        self.assertAlmostEqual(7.0, productA.virtual_available, 
                               "virtual_available NOK, found %s instead of 7.0" % productA.virtual_available)
        print "self.productA.virtual_available : ", productA.virtual_available
        print "OK, 7"

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


