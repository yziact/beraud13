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


    ### basic reservation ###
    def test_stock_picking_simple_reserve(self):
        print "test_stock_picking_simple_reserve" 

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
            'company_id': 1,
            'qty': 0.0,
        })

        print "CUSTOMER LOC ID : %s ", self.customer_loc_id
        print "BER LOC ID : %s ",  self.ber_loc_id
        print "ATOM LOC ID : %s ",  self.atom_loc_id
        print "PARTNER ID : %s ", self.partner_ber_id

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

    def test_stock_picking_reserve_with_tsis(self):
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
            'company_id': 1,
            'qty': 2.0,
        })

        print "CUSTOMER LOC ID : %s ", self.customer_loc_id
        print "BER LOC ID : %s ",  self.ber_loc_id
        print "ATOM LOC ID : %s ",  self.atom_loc_id
        print "PARTNER ID : %s ", self.partner_ber_id

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
        print "assigned."
        model = self.env.context.get('active_model')
        print "model is : ", model


