# -*- coding: utf-8 -*-

from . import common 
from openerp.tools import mute_logger, float_round

import logging
_logger = logging.getLogger(__name__)

class TestsReparations(common.TestsCommon):

    #@mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def setUp(self):
        super(TestsReparations, self).setUp()

        self.partner_ber_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',1)])
        self.partner_atom_id = self.PartnerObj.search([('name','ilike','2 CARA'),('company_id','=',3)])

        self.ber_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        self.atom_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        self.customer_loc_id = self.LocObj.search([('complete_name','ilike','Partner Locations/Customers')])

        # get Nicolas Clair
        self.beraud_partner_id = self.env['res.partner'].search([('name','ilike','Nicolas Clair')])
        self.beraud_user_id = self.env['res.users'].search([('partner_id','=',self.beraud_partner_id.id)])

    ### basic company site repair ###
    def test00_company_repair(self):
        """
        Repair for a customer of Beraud in Beraud site. Invoice method after repair.
        """

        print "test00_company_repair" 

        # create product and quants for product
        productA = self.ProductObj.create({'name': 'Product A'})
        productB = self.ProductObj.create({'name': 'Product B'})

        # quants for A
        self.QuantObj.create({
            'product_id': productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })

        # quants for B
        self.QuantObj.create({
            'product_id': productB.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })

        # repair and repair line
        repair_id = self.RepairObj.create({
            'partner_id': self.partner_ber_id.id,
            'product_id': productA.id,
            'product_uom': productA.uom_id.id,
            #'address_id': self.partner_ber_id.contact_address.id, 
            'invoice_method': 'after_repair',
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
        })

        self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            'location_id': self.ber_loc_id.id,
            'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': productB.id,
            'product_uom': productB.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'add',
        })

        #repair_id.repair_confirm()
        repair_id.sudo(self.beraud_user_id.id).repair_confirm()

        self.assertAlmostEqual(7.0, productA.virtual_available)
        print "self.productA.virtual_available : ", productA.virtual_available
        print "OK"


