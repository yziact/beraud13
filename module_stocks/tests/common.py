# -*- coding: utf-8 -*-

from openerp.tests import common

class TestsCommon(common.TransactionCase):

    def setUp(self):
        super(TestsCommon, self).setUp()

        # some users
        #group_manager = self.env.ref('base.group_sale_manager')
        #group_user = self.env.ref('base.group_sale_salesman')
        group_user = self.env.ref('base.group_user')
        inventory_user = self.env.ref('base.group_user')

        """
        self.manager = self.env['res.users'].create({
            'name': 'Andrew Manager',
            'login': 'manager',
            'alias_name': 'andrew',
            'email': 'a.m@example.com',
            'signature': '--\nAndreww',
            'notify_email': 'always',
            'groups_id': [(6, 0, [group_manager.id])]
        })

        self.user_beraud = self.env['res.users'].create({
            'name': 'Beraud User',
            'login': 'userberaud',
            'alias_name': 'beraud_user_alias',
            'email': 'm.u@example.com',
            'signature': '--\nMark',
            'notify_email': 'none',
            'groups_id': [(6, 0, [group_user.id])],
            'company_id': 1,
        })

        self.user_atom = self.env['res.users'].create({
            'name': 'Atom User',
            'login': 'useratom',
            'alias_name': 'atom_user_alias',
            'email': 'm.u@example.com',
            'signature': '--\nMark',
            'notify_email': 'none',
            'groups_id': [(6, 0, [group_user.id])],
            'company_id': 1,
        })
        """

        #self.partner = self.env.ref('base.res_partner_1')
        self.ProductObj = self.env['product.product']
        self.UomObj = self.env['product.uom']
        self.PartnerObj = self.env['res.partner']
        self.ModelDataObj = self.env['ir.model.data']
        self.StockPackObj = self.env['stock.pack.operation']
        self.StockQuantObj = self.env['stock.quant']
        self.PickingObj = self.env['stock.picking']
        self.MoveObj = self.env['stock.move']
        self.InvObj = self.env['stock.inventory']
        self.InvLineObj = self.env['stock.inventory.line']
        #self.LotObj = self.env['stock.production.lot']
        self.LocObj = self.env['stock.location']
        self.QuantObj = self.env['stock.quant']

        # Model Data
        #self.partner_agrolite_id = self.ModelDataObj.xmlid_to_res_id('base.res_partner_2')
        #self.partner_delta_id = self.ModelDataObj.xmlid_to_res_id('base.res_partner_4')
        self.picking_type_in = self.ModelDataObj.xmlid_to_res_id('stock.picking_type_in')
        self.picking_type_out = self.ModelDataObj.xmlid_to_res_id('stock.picking_type_out')
        self.supplier_location = self.ModelDataObj.xmlid_to_res_id('stock.stock_location_suppliers')
        self.stock_location = self.ModelDataObj.xmlid_to_res_id('stock.stock_location_stock')
        self.stock_location_beraud = self.ModelDataObj.xmlid_to_res_id('stock.stock_location_stock')
        self.stock_location_atom = self.ModelDataObj.xmlid_to_res_id('stock.stock_location_stock')
        self.customer_location = self.ModelDataObj.xmlid_to_res_id('stock.stock_location_customers')
        self.categ_unit = self.ModelDataObj.xmlid_to_res_id('product.product_uom_categ_unit')
        self.categ_kgm = self.ModelDataObj.xmlid_to_res_id('product.product_uom_categ_kgm')

        # Product Created A, B, C, D
        #self.productA = self.ProductObj.create({'name': 'Product A'})
        #self.productB = self.ProductObj.create({'name': 'Product B'})
        #self.productC = self.ProductObj.create({'name': 'Product C'})
        #self.productD = self.ProductObj.create({'name': 'Product D'})

        # Configure unit of measure.
        self.uom_kg = self.UomObj.create({
            'name': 'Test-KG',
            'category_id': self.categ_kgm,
            'factor_inv': 1,
            'factor': 1,
            'uom_type': 'reference',
            'rounding': 0.000001})
        self.uom_tone = self.UomObj.create({
            'name': 'Test-Tone',
            'category_id': self.categ_kgm,
            'uom_type': 'bigger',
            'factor_inv': 1000.0,
            'rounding': 0.001})
        self.uom_gm = self.UomObj.create({
            'name': 'Test-G',
            'category_id': self.categ_kgm,
            'uom_type': 'smaller',
            'factor': 1000.0,
            'rounding': 0.001})
        self.uom_mg = self.UomObj.create({
            'name': 'Test-MG',
            'category_id': self.categ_kgm,
            'uom_type': 'smaller',
            'factor': 100000.0,
            'rounding': 0.001})
        # Check Unit
        self.uom_unit = self.UomObj.create({
            'name': 'Test-Unit',
            'category_id': self.categ_unit,
            'factor': 1,
            'uom_type': 'reference',
            'rounding': 1.0})
        self.uom_dozen = self.UomObj.create({
            'name': 'Test-DozenA',
            'category_id': self.categ_unit,
            'factor_inv': 12,
            'uom_type': 'bigger',
            'rounding': 0.001})
        self.uom_sdozen = self.UomObj.create({
            'name': 'Test-SDozenA',
            'category_id': self.categ_unit,
            'factor_inv': 144,
            'uom_type': 'bigger',
            'rounding': 0.001})
        self.uom_sdozen_round = self.UomObj.create({
            'name': 'Test-SDozenA Round',
            'category_id': self.categ_unit,
            'factor_inv': 144,
            'uom_type': 'bigger',
            'rounding': 1.0})

        # Product for different unit of measure.
        self.DozA = self.ProductObj.create({'name': 'Dozon-A', 'uom_id': self.uom_dozen.id, 'uom_po_id': self.uom_dozen.id})
        self.SDozA = self.ProductObj.create({'name': 'SuperDozon-A', 'uom_id': self.uom_sdozen.id, 'uom_po_id': self.uom_sdozen.id})
        self.SDozARound = self.ProductObj.create({'name': 'SuperDozenRound-A', 'uom_id': self.uom_sdozen_round.id, 'uom_po_id': self.uom_sdozen_round.id})
        self.UnitA = self.ProductObj.create({'name': 'Unit-A'})
        self.kgB = self.ProductObj.create({'name': 'kg-B', 'uom_id': self.uom_kg.id, 'uom_po_id': self.uom_kg.id})
        self.gB = self.ProductObj.create({'name': 'g-B', 'uom_id': self.uom_gm.id, 'uom_po_id': self.uom_gm.id})


    def print_quant(self, q):
        print "quant id : ", q.id
        print "quant name : ", q.name
        print "quant product_id : ", q.product_id
        print "quant location_id : ", q.location_id
        print "quant company_id : ", q.company_id
        print "quant qty : ", q.qty

