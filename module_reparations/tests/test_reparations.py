# -*- coding: utf-8 -*-

from . import common 
from openerp.tools import mute_logger, float_round

import logging
_logger = logging.getLogger(__name__)

class bcolors:
    PURPLE = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestsReparations(common.TestsCommon):

    #@mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def setUp(self):
        super(TestsReparations, self).setUp()

        self.partner_ber_id = self.PartnerObj.search([('name','ilike','123 COURROIES'),('company_id','=',1)])
        self.partner_atom_id = self.PartnerObj.search([('name','ilike','123 COURROIES'),('company_id','=',3)])

        self.ber_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        self.atom_loc_id = self.LocObj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        self.customer_loc_id = self.LocObj.search([('complete_name','ilike','Partner Locations/Customers')])

        #self.beraud_partner_id = self.env['res.partner'].search([('name','ilike','Nicolas Clair')])
        #self.beraud_partner_id = self.env['res.partner'].search([('name','ilike','Etienne Laurent')])
        #self.beraud_user_id = self.env['res.users'].search([('partner_id','=',self.beraud_partner_id.id)])

        user_group_employee = self.env.ref('base.group_user')
        group_obj = self.env['res.groups']
        groupe_technique = group_obj.search([('name','ilike','TECHNIQUE')])
        print "groupe_technique : ", groupe_technique

        # Test users to use through the various tests
        Users = self.env['res.users'].with_context({'no_reset_password': True, 'mail_create_nosubscribe': True})
        self.beraud_user = Users.create({
            'company_id' : 1,
            'name': 'Jean Reparations',
            'login': 'jeanr',
            'alias_name': 'jeanr',
            'email': 'jeanrexample.com',
            'groups_id': [(6, 0, [user_group_employee.id, groupe_technique.id])]})

        self.atom_tech = Users.create({
            #'company_id' : 3,
            'name': 'Jean Tech Atom',
            'login': 'jeantechatom',
            'alias_name': 'jeantechatom',
            'email': 'jeantechatomexample.com',
            'groups_id': [(6, 0, [user_group_employee.id, groupe_technique.id])]})

        tech_loc_id = self.LocObj.search([('name','like','94')])
        tech_loc_id.tech = self.atom_tech.id
        print "tech_loc_id.name", tech_loc_id.name

        # create product and quants for product
        #self.productA = self.ProductObj.create({'name': 'Product A'})
        #self.productB = self.ProductObj.create({'name': 'Product B'})
        #self.productC = self.ProductObj.create({'name': 'Product C'})
        #self.productD = self.ProductObj.create({'name': 'Product D'})
        #self.productE = self.ProductObj.create({'name': 'Product E'})
        self.productA = self.ProductObj.search([('id','=','59004')])
        self.productB = self.ProductObj.search([('id','=','59005')])
        self.productC = self.ProductObj.search([('id','=','59006')])
        self.productD = self.ProductObj.search([('id','=','59007')])
        self.productE = self.ProductObj.search([('id','=','59008')])

        print "productA : ", self.productA.name
        print "productB : ", self.productB.name
        print "productC : ", self.productC.name
        print "productD : ", self.productD.name
        print "productE : ", self.productE.name
 
        self.QuantObj.create({
            'product_id': self.productA.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })
        self.QuantObj.create({
            'product_id': self.productB.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })
        self.QuantObj.create({
            'product_id': self.productC.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })
        self.QuantObj.create({
            'product_id': self.productD.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })
        self.QuantObj.create({
            'product_id': self.productE.id,
            'location_id': self.ber_loc_id.id,
            'company_id': 1,
            'qty': 10.0,
        })

    ### basic in-company (no tech) repair ###
    def test00_repair_no_tech(self):
        """
        Repair for a customer of Beraud in Beraud site. Invoice method after repair.
        """

        print "test00_repair_no_tech" 

        return

        # repair and repair line
        print "self.partner_ber_id : ", self.partner_ber_id
        repair_id = self.RepairObj.create({
            'partner_id': self.partner_ber_id.id,
            'product_id': self.productA.id,
            'product_uom': self.productA.uom_id.id,
            #'address_id': self.partner_ber_id.contact_address.id, 
            #'invoice_method': 'after_repair',
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
        })

        print "repair_id.location_id.name : ", repair_id.location_id.name
        print "repair_id.location_dest_id.name : ", repair_id.location_dest_id.name

        self.assertEqual(repair_id.location_id.name, 'Reparations' )
        self.assertEqual(repair_id.location_dest_id.name, 'Customers')
        self.assertEqual(repair_id.invoice_method, 'after_repair')

        self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productB.id,
            'product_uom': self.productB.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'add',
        })

        self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productC.id,
            'product_uom': self.productC.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'remove',
        })

        #repair_id.repair_confirm()
        repair_id.sudo(self.beraud_user.id).action_confirm()

        # check linked moves
        """
        for move in repair_id.linked_moves :
            print "======= (%s - %s) ======" % (move.name, move.id)
            print "======= location_id : ", move.location_id.name
            print "======= location_dest_id : ", move.location_dest_id.name
            print "======= partner_id : ", move.partner_id
            print "======= product_id : ", move.product_id
            print "======= partner_uom_qty : ", move.product_uom_qty
        """

        print bcolors.OKGREEN+"repair_id.state : "+repair_id.state+bcolors.ENDC

        self.assertEqual(repair_id.state, 'confirmed')

        # adding a line when repair is in state 'confirmed'
        line_id = self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productC.id,
            'product_uom': self.productC.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'remove',
        })

        self.assertEqual(line_id.location_id.name, 'Customers', msg='line_id.location_id is wrong : %s' % line_id.location_id.name)
        self.assertEqual(line_id.location_dest_id.name, 'Stock', msg='line_id.location_dest_id is wrong : %s' % line_id.location_dest_id.name)
        print bcolors.OKGREEN+"line_id REMOVE associated_move : ", line_id.associated_move, bcolors.ENDC

        # adding a line when repair is in state 'confirmed'
        line_id = self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productC.id,
            'product_uom': self.productC.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'add',
        })

        self.assertEqual(line_id.location_id.name, 'Stock', msg='line_id.location_id is wrong : %s' % line_id.location_id.name)
        self.assertEqual(line_id.location_dest_id.name, 'Production', msg='line_id.location_dest_id is wrong : %s' % line_id.location_dest_id.name)
        print bcolors.OKGREEN+"line_id ADD associated_move : ", line_id.associated_move, bcolors.ENDC

        repair_id.sudo(self.beraud_user.id).action_repair_end()

        # check that the moves are all done
        for move in repair_id.linked_moves:
            self.assertEqual(move.state, 'done', msg='move.state is not done : %s' % move.state)

        # check the bl is confirmed
        self.assertEqual(repair_id.bl.state, 'confirmed', msg='repair_id.bl.state is not confirmed : %s' % repair_id.bl.state)


    ### on customer site (there's a tech) repair ###
    def test01_repair_with_tech(self):
        """
        Repair on a Customer Site. A tech goes the the Customer site and repairs the machine there.
        """

        print "test01_repair_with_tech" 

        # repair and repair line
        print "self.partner_ber_id : ", self.partner_ber_id
        repair_id = self.RepairObj.create({
            'partner_id': self.partner_ber_id.id,
            'product_id': self.productA.id,
            'product_uom': self.productA.uom_id.id,
            'tech': self.atom_tech.id,
            #'address_id': self.partner_ber_id.contact_address.id, 
            #'invoice_method': 'after_repair',
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'clientsite': True
        })

        print "repair_id.location_id.name : ", repair_id.location_id.name
        print "repair_id.location_dest_id.name : ", repair_id.location_dest_id.name
        print "repair_id.tech.name : ", repair_id.tech.name

        self.assertEqual(repair_id.location_id.name, 'Reparations' )
        self.assertEqual(repair_id.location_dest_id.name, 'Customers')
        self.assertEqual(repair_id.invoice_method, 'after_repair')
        self.assertEqual(repair_id.tech.name, 'Jean Tech Atom')

        self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productB.id,
            'product_uom': self.productB.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'add',
        })

        self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productC.id,
            'product_uom': self.productC.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'remove',
        })

        #repair_id.repair_confirm()
        repair_id.sudo(self.beraud_user.id).action_confirm()

        # check linked moves
        """
        for move in repair_id.linked_moves :
            print "======= (%s - %s) ======" % (move.name, move.id)
            print "======= location_id : ", move.location_id.name
            print "======= location_dest_id : ", move.location_dest_id.name
            print "======= partner_id : ", move.partner_id
            print "======= product_id : ", move.product_id
            print "======= partner_uom_qty : ", move.product_uom_qty
        """

        tech_loc_id = 41
        customer_loc_id = 9
        stock_loc_id = 9

        self.assertEqual(repair_id.state, 'confirmed')
        print bcolors.OKGREEN+"repair_id.state : "+repair_id.state+bcolors.ENDC

        # adding a line when repair is in state 'confirmed'
        line_id = self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productC.id,
            'product_uom': self.productC.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'remove',
        })

        #import pudb;pudb.set_trace()
        #print "line_id.location_id.name : %s" % line_id.location_id.name
        #print "line_id.location_dest_id.name : ", line_id.location_dest_id.name

        # validate the internal BL
        repair_id.bl_internal.action_assign()
        repair_id.bl_internal.action_done()
        self.assertEqual(repair_id.bl_internal.state, 'done', msg='BL Internal in wrong state : %s' % repair_id.bl_internal.state)

        repair_id.sudo(self.beraud_user.id).action_repair_end()

        print "looking for moves generated by the end of the repair"
        moves_generated = self.MoveObj.search([('origin','ilike', repair_id.name)])
        print "moves_generated : ", moves_generated

        # make sure that none of the moves are isSale
        for move in moves_generated:
            self.assertEqual(move.isSale, False, msg='move.isSale is not False : %s' % move.isSale)

        """
        import pudb;pudb.set_trace()
        for move in moves_generated : 
            print "move.isSale : %s, %s" % (move.id, move.isSale)
        """

        """
        self.assertEqual(line_id.location_id.name, 'Customers', msg='line_id.location_id is wrong : %s' % line_id.location_id.name)
        self.assertEqual(line_id.location_dest_id.name, '94', msg='line_id.location_dest_id is wrong : %s' % line_id.location_dest_id.name)
        print bcolors.OKGREEN+"line_id REMOVE associated_move : ", line_id.associated_move, bcolors.ENDC

        # adding a line when repair is in state 'confirmed'
        line_id = self.RepairLineObj.create({
            'repair_id': repair_id.id,
            'name': repair_id.name,
            #'location_id': self.ber_loc_id.id,
            #'location_dest_id': self.customer_loc_id.id,
            'price_unit': 50.0,
            'product_id': self.productC.id,
            'product_uom': self.productC.uom_id.id,
            'product_uom_qty': 2.0,
            'to_invoice': 1,
            'type': 'add',
        })

        self.assertEqual(line_id.location_id.name, 'Stock', msg='line_id.location_id is wrong : %s' % line_id.location_id.name)
        self.assertEqual(line_id.location_dest_id.name, '94', msg='line_id.location_dest_id is wrong : %s' % line_id.location_dest_id.name)
        print bcolors.OKGREEN+"line_id ADD associated_move : ", line_id.associated_move, bcolors.ENDC

        repair_id.sudo(self.beraud_user.id).action_repair_end()
        """
        """

        # check that the moves are all done
        for move in repair_id.linked_moves:
            self.assertEqual(move.state, 'done', msg='move.state is not done : %s' % move.state)

        # check the bl is confirmed
        self.assertEqual(repair_id.bl.state, 'confirmed', msg='repair_id.bl.state is not confirmed : %s' % repair_id.bl.state)
        """


