# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
from utilsmod import utilsmod
from openerp.exceptions import UserError

import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import logging 
_logger = logging.getLogger(__name__)

import pprint
pp = pprint.PrettyPrinter(indent=2)

class MrpRepairInh(models.Model):
    _inherit = 'mrp.repair'

    def _set_default_end_date(self):
        return (datetime.datetime.now()+datetime.timedelta(days=1)).strftime(DATETIME_FORMAT)

    def _set_default_location(self):
        ber_loc_id = self.env['stock.location'].search([('complete_name','ilike','Physical Locations/DC/Stock')])
        return ber_loc_id

    #def _task_domain(self):
    #    return [('name', 'ilike', self.name)]

    # override workflow states
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('valid', u'Devis Validé'),
        ('confirmed', 'Confirmed'),
        ('under_repair', 'Under Repair'),
        ('ready', 'Ready to Repair'),
        ('2binvoiced', 'To be Invoiced'),
        ('invoice_except', 'Invoice Exception'),
        ('done', 'Repaired'),
        ('cancel', 'Cancelled')
    ], 'Status', readonly=True, track_visibility='onchange', copy=False, store=True, default='draft',
        help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed repair order. \
        \n* The \'Confirmed\' status is used when a user confirms the repair order. \
        \n* The \'Ready to Repair\' status is used to start to repairing, user can start repairing only after repair order is confirmed. \
        \n* The \'To be Invoiced\' status is used to generate the invoice before or after repairing done. \
        \n* The \'Done\' status is set when repairing is completed.\
        \n* The \'Cancelled\' status is used when user cancel repair order.')

    # not visible to the model until created, but exists in db
    create_date = fields.Datetime('Create Date', readonly=True)

    date_start = fields.Datetime(string='Date de début', required=True, store=True,
                                 default=fields.Datetime.now, help="Date du début de la réparation")

    end_date = fields.Datetime(string="Date de fin", store=True, help="Date prévue de la fin de la réparation",
                              default=_set_default_end_date)

    invoice_method = fields.Selection(default='after_repair')
    clientsite = fields.Boolean(string="Réparation sur Site Client : ", default=False)

    tech = fields.Many2one('res.users', string="Technicien", domain=[('company_id','in',[1,3])], company_dependent=False) 

    operations = fields.One2many('mrp.repair.line', 'repair_id', 'Operation Lines', readonly=False, copy=True)

    location_id = fields.Many2one('stock.location', string='Current Location', 
                                  select=True, required=True, readonly=True,
                                  states={'draft': [('readonly', True)], 'confirmed': [('readonly', True)]},
                                  default=_set_default_location)

    location_dest_id = fields.Many2one('stock.location', string='Delivery Location',
                                       readonly=True, required=True,
                                       states={'draft': [('readonly', True)], 'confirmed': [('readonly', True)]},
                                       default=_set_default_location)

    # bl and br for beraud site repairs
    bl = fields.Many2one('stock.picking')
    br = fields.Many2one('stock.picking')

    # internal bl, from stock to tech stock, for client site repairs
    bl_internal = fields.Many2one('stock.picking')

    # task associated to 
    task_id = fields.Many2one('project.task')

    def open_task_line(self, cr, uid, ids, context=None):
        print "open_task_like button clicked"

        for repair in self.browse(cr, uid, ids, context={}) :
            print "task_id : ", repair.task_id
            return {
                "type": "ir.actions.act_window",
                "res_model": "project.task",
                "views": [[False, "form"]],
                "res_id": repair.task_id.id,
                #"target": "new",
                "target": "current",
            }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        mask = utilsmod.ReportMask(['module_reparations.report_repair_devis',
                                    'module_reparations.report_no_prices'])
        res = super(MrpRepairInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(res, self)

    @api.onchange('clientsite') 
    def clientsite_change(self):
        print "clientsite has changed !"
        if not self.clientsite:
            self.tech = None

    @api.onchange('tech') 
    def tech_change(self):
        print "tech has changed !"
        if not self.tech:
            return
        else:
            self._set_dest_of_lines()

    def action_repair_validate(self, cr, uid, ids, context=None):
        print "mrp_repair our action_validate"
        for repair in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [repair.id], {'state': 'valid'}, context=context)

    def _set_dest_of_lines(self, new_tech=None):
        print "_set_dest_of_lines"

        loc_obj = self.env["stock.location"]
        t_obj = self.env['res.users']
        orig_loc_id = 0
        dest_loc_id = 0
        print '[sdol]self.tech : ', self.tech
        print '[sdol]new_tech : ', new_tech

        customer_loc_id = loc_obj.search([('complete_name','ilike','Partner Locations/Customers')])
        prod_loc_id = loc_obj.search([('complete_name','ilike','Virtual Locations/Production')])

        for line in self.operations:
            if new_tech:
                new_tech_name = t_obj.browse(new_tech).name
                orig_loc_id = self.location_id
                dest_loc_id = loc_obj.search([('tech', 'ilike', new_tech_name)])
                print "--> new tech, dest_loc_id : ", dest_loc_id
                if not dest_loc_id:
                    raise UserError("[gslfr] Le Technicien spécifié n'a pas d'emplacement de stock assigné")
            #False means we changed from a tech to None, None means we didn't pass anything
            elif self.tech and new_tech != False: 
                orig_loc_id = self.location_id
                dest_loc_id = loc_obj.search([('tech', 'ilike', self.tech.name)])
                print "--> tech, dest_loc_id : ", dest_loc_id
                if not dest_loc_id:
                    raise UserError("[gslfr] Le Technicien spécifié n'a pas d'emplacement de stock assigné")
            else:
                if line.type == 'add':
                    orig_loc_id = self.location_id
                    dest_loc_id = prod_loc_id
                else :
                    orig_loc_id = customer_loc_id
                    dest_loc_id = self.location_id
                print "--> NO TECH, dest_loc_id : ", dest_loc_id
                if not dest_loc_id:
                    raise UserError("[gslfr] Emplacement Virtuel de Production non trouvé.")

            line.write({ 'location_id':orig_loc_id.id })
            line.write({ 'location_dest_id':dest_loc_id.id })

    @api.model
    def create(self, vals):
        print "***mrp repair our create"

        print "vals : "
        pp.pprint(vals)

        ### set location_id/dest_id of repair
        if not vals['partner_id']:
            print "partner_id empty in vals in create"
            raise UserError("Il faut un partenaire pour sélectionner les emplacements source/destination")

        partner_obj = self.env['res.partner']
        p_obj = self.env['product.product']
        t_obj = self.env['res.users']
        l_obj = self.env['stock.location']

        ber_loc_id = l_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        atom_loc_id = l_obj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        customer_loc_id = l_obj.search([('complete_name','ilike','Partner Locations/Customers')])

        production_loc_id = l_obj.search([('complete_name','ilike','Virtual Locations/Production')])
        remove_loc_id = l_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])

        c_id = partner_obj.browse(vals['partner_id']).company_id.id
        print "c_id : ", c_id

        vals['location_id'] = ber_loc_id.id
        remove_loc_id = ber_loc_id

        if c_id == 3:
            vals['location_id'] = atom_loc_id.id
            remove_loc_id = atom_loc_id

        vals['location_dest_id'] = customer_loc_id.id

        ### set location_id/dest_id of repair_lines
        p_obj = self.env['product.product']
        t_obj = self.env['res.users']
        l_obj = self.env['stock.location']

        if vals['operations']:
            for v in vals['operations']:
                o = v[2]
                print "o was : ", o
                l_id = p_obj.browse(o['product_id']).location_id
                l_id = vals['location_id'] # product is taken from the stock set in the repair
                if o.get('type') == 'add':
                    ld_id = production_loc_id.id
                else :
                    l_id = customer_loc_id.id
                    ld_id = remove_loc_id.id

                # if there's a tech, change the dest location
                # even if the line is destined to be 'removed',
                # cause the first move will be stock->tech even so.
                if vals['tech']:
                    print "there is a tech selected : ", vals['tech']
                    t_name = t_obj.browse(vals['tech']).name
                    t_loc = l_obj.search([('tech', 'ilike', t_name)])
                    print "t_name : ", t_name
                    print "t_loc : ", t_loc
                    ld_id = t_loc.id

                o.update({'location_id': l_id})
                o.update({'location_dest_id': ld_id})
                print "o is now: ", o

        rec = super(MrpRepairInh, self).create(vals)
        return rec

    @api.multi
    def write(self, vals):
        print "*** mrp_repair our write"

        p_obj = self.env['product.product']
        t_obj = self.env['res.users']
        l_obj = self.env['stock.location']
        print "vals : "
        pp.pprint(vals)

        production_loc_id = l_obj.search([('complete_name','ilike','Virtual Locations/Production')])

        remove_loc_id = self.location_id

        print "self.location_id : ", self.location_id
        print "self.location_dest_id : ", self.location_dest_id
        print "self.tech : ", self.tech

        # add locations to updates to operations
        if vals.get('operations'): # operation lines and maybe also tech were changed
            print "operations have changed"
            for v in vals['operations']:
                o = v[2]
                if not o:
                    continue
                print "o was : ", o
                #l_id = p_obj.browse(o['product_id']).location_id
                l_id = self.location_id.id # product is taken from the stock set in the repair
                if o.get('type') == 'add':
                    ld_id = production_loc_id.id
                else:
                    ld_id = remove_loc_id.id

                # if there's a tech, change the dest location
                if self.tech or o.get('tech'):
                    print "there's a tech already set (self.tech) : ", self.tech
                    print "new_tech : ", self.tech
                    t_name = t_obj.browse(self.tech.id).name
                    t_loc = l_obj.search([('tech', 'ilike', t_name)])
                    print "t_name : ", t_name
                    print "t_loc : ", t_loc
                    ld_id = t_loc.id

                o.update({'location_id': l_id})
                o.update({'location_dest_id': ld_id})
                print "o is now: ", o

        print "[write] vals.get('tech') : ", vals.get('tech')
        print "[write] self.tech : ", self.tech

        print 'end vals : ', vals
        # check that all lines destinations are correct,
        # in function of if the tech was removed or is set.
        
        rec = super(MrpRepairInh, self).write(vals)
        self._set_dest_of_lines(vals.get('tech'))
        return rec

    def action_confirm(self, cr, uid, ids, context):

        print "mrp_repair our action_confirm"

        # need to call this first for the serial ids checks
        # and the state changes related to invoicing (2binvoiced or confirmed)
        # but this doesn't make any moves
        res = super(MrpRepairInh, self).action_confirm(cr, uid, ids, context)

        sp_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        loc_obj = self.pool.get("stock.location")
        proj_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        move_list = []

        for repair in self.browse(cr, uid, ids, context={}) :

            # create the task in project 'SAV'
            proj_name = 'REPARATIONS ATELIER'
            if repair.clientsite : 
                proj_name = 'SAV'

            p_id = proj_obj.search(cr, uid, [('name', 'ilike', proj_name)])
            project_id = proj_obj.browse(cr, uid, p_id)

            if not project_id : 
                raise UserError("Aucun projet '%s' trouvé." % proj_name)

            task_id = task_obj.create(cr, uid, {
                'project_id' : project_id.id,
                'name' : repair.name,
                'partner_id' : repair.partner_id.id,
            })
            
            print "task créée, id : ", task_id
            repair.task_id = task_id

            src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
            wh = loc_obj.get_warehouse(cr, uid, src_loc, context={})

### BERAUD SITE REPAIR CONFIRM CASE ###
            if not repair.clientsite:
                # the picking type is always incoming, but depends on the warehouse it comes from...
                # this will determine the sequence of the generated stock picking
                print "SRC LOC : %s" % src_loc
                print "WH : %s" % wh

                picking_type_in = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', wh)])
                print "picking type in : %s" % picking_type_in

                picking_type_out = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'outgoing'), ('warehouse_id', '=', wh)])
                print "picking type out : %s" % picking_type_out

                if not picking_type_in:
                    raise UserError("Something went wrong while selecting the picking type in.")
                if not picking_type_out:
                    raise UserError("Something went wrong while selecting the picking type out.")

                ### CREATE BR
                # create it in draft, then immediately set it to 'todo'
                # confirm does that

                picking_id = sp_obj.create(cr, uid, {
                    'origin':repair.name,
                    'partner_id': repair.partner_id.id, 
                    'picking_type_id': picking_type_in[0],
                    'move_type': 'direct',
                    'location_id': repair.location_dest_id.id, # comes from the client location
                    'location_dest_id': repair.location_id.id, # to our location 
                })

                # add article to repair to the picking (we'll receive it to repair it)
                move_id = move_obj.create(cr, uid, {
                    'origin': repair.name,
                    'name': repair.product_id.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_id.uom_id.id,
                    'product_uom_qty': abs(repair.product_qty),
                    'picking_id': picking_id,
                    'picking_type_id': picking_type_in[0],
                    #'state': 'draft',
                    'location_id': repair.location_dest_id.id, # client location to
                    'location_dest_id': repair.location_id.id, # our location
                    'restrict_lot_id': repair.lot_id.id,
                }, context={})

                if picking_id:
                    print "confirming BR."
                    res = sp_obj.action_confirm(cr, uid, [picking_id], context=context)
                    print "res : ", res
                    if not res:
                        raise UserError("Something went wrong while confirming stock_picking")
                else:
                    raise UserError("Something went wrong while creating stock_picking")

                print "to br"
                repair.br = picking_id
                print "BR created : %s" % sp_obj.browse(cr, uid, picking_id, context={}).name


                ### Create picking BL
                # we create in in draft mode (default)
                # We'll deliver the article after having it fixed
                # Create move corresponding to repaired article, added to the picking

                picking_id = sp_obj.create(cr, uid, {
                    'origin':repair.name,
                    'product_id': repair.product_id.id,
                    'partner_id': repair.partner_id.id, 
                    'picking_type_id': picking_type_out[0],
                    'location_id': repair.location_id.id, 
                    'location_dest_id': repair.location_dest_id.id,
                })

                # adding repaired product to BL
                move_id = move_obj.create(cr, uid, {
                    'origin':repair.name,
                    'name': repair.product_id.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                    'product_uom_qty': repair.product_qty,
                    'partner_id': repair.address_id and repair.address_id.id or False,
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                    'picking_id': picking_id,
                    'picking_type_id': picking_type_out[0],
                    'restrict_lot_id': repair.lot_id.id,
                })

                if not move_id:
                    raise UserError("Something went wrong while creating move for BL")

                print "to bl"
                repair.bl = picking_id
                print "BL created : %s" % sp_obj.browse(cr, uid, picking_id, context={}).name

### CLIENT SITE REPAIR CONFIRM CASE ###
            elif repair.clientsite:

                if not repair.tech:
                    raise UserError("Technicien non-spécifié")

                # get stock location corresponding to technician
                t_loc_id = loc_obj.search(cr, uid, [('tech', 'ilike', repair.tech.name)])
                tech_loc_id = loc_obj.browse(cr, uid, t_loc_id)

                if not tech_loc_id:
                    raise UserError("Le Technicien spécifié n'a pas d'emplacement de stock assigné")

                # confirm stage : create bl_internal from stock to tech location, in draft state
                # add repair lines to this bl_internal

                picking_type_internal = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'internal'), ('warehouse_id', '=', wh),
                              ('name', '=', 'Transfert techniciens')])
                print "picking type internal : %s" % picking_type_internal

                picking_id = sp_obj.create(cr, uid, {
                    'origin':repair.name,
                    'product_id': repair.product_id.id,
                    'partner_id': repair.partner_id.id, 
                    'picking_type_id': picking_type_internal[0],
                    'location_id': repair.location_id.id, 
                    'location_dest_id': tech_loc_id.id,
                })

                for line in repair.operations:
                    print "creating move : %s" % line.name
                    # add move lines to the picking
                    move_id = move_obj.create(cr, uid, {
                        'origin': repair.name,
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': abs(line.product_uom_qty),
                        'picking_id': picking_id,
                        'picking_type_id': picking_type_internal[0],
                        'location_id': line.location_id.id, # line location
                        'location_dest_id': line.location_dest_id.id, #line location
                        'restrict_lot_id': line.lot_id.id,
                    })
                    if not move_id:
                        raise UserError("Problème survenu lors de la création du BL interne vers le technicien")
                    m = move_obj.browse(cr, uid, move_id)
                    print "Client site repair"
                    print "Create moves and added to bl_internal picking (From stock location to tech location)"
                    print "move_id : ", m.id
                    print "quants of move : ", m.quant_ids

                print "Created moves and added them to the BL_INTERNAL (From stock location to tech location)"
                repair.bl_internal = picking_id
                print "repair.bl_internal : ", repair.bl_internal

        return res

    def action_repair_done(self, cr, uid, ids, context=None):
        """
        sets repair as done
        """
        print "Mrp_repair our action_repair_done"
        for repair in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [repair.id], {'state': 'done'}, context=context)

    def action_repair_end(self, cr, uid, ids, context=None):
        """ Creates stock move for operation and stock move for final product of repair order.
        @return: Move ids of final products
        """
        """ COMPLETE REWRITE OF ACTION_REPAIR_DONE """
        """ had to be rewritten because the moves created had no picking parent so they didn't appear
        anywhere in any picking and I could not reparent them even by setting the picking_ids correctly.
        As a result doing something like super(..).action_repair_done() did not do good things, even if the
        function did return the move_id.
        The moves will now be created for all the pieces used for the repair, and the move for the
        repaired piece will figure on a generated BL"""
        
        print "Mrp_repair our action_repair_end"

        super(MrpRepairInh, self).action_repair_end(cr, uid, ids, context=context)
        res = {}
        move_obj = self.pool.get('stock.move')
        repair_line_obj = self.pool.get('mrp.repair.line')
        loc_obj = self.pool.get("stock.location")
        sp_obj = self.pool.get('stock.picking')

        for repair in self.browse(cr, uid, ids, context=context):
### BERAUD SITE REPAIR DONE CASE ###
            if not repair.clientsite:

                # each repair line will go to where it was supposed to.
                # No need to create BL/BR for them
                # we set the BL from 'draft' to 'todo'
                # by confirming it
                #bl_id = sp_obj.search(cr, uid, [(' ', ' ', ' ')])
                print "going to confirm BL : ", repair.bl
                repair.bl.action_confirm()

                # take lines in the OR and perform moves, to done.
                for line in repair.operations:
                    print "creating move : %s" % line.name
                    # add move lines to the picking
                    move_id = move_obj.create(cr, uid, {
                        'origin': repair.name,
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': abs(line.product_uom_qty),
                        'location_id': line.location_id.id, # line location
                        'location_dest_id': line.location_dest_id.id, #line location
                        'restrict_lot_id': line.lot_id.id,
                    })
                    # make them done
                    move_obj.action_done(cr, uid, move_id)

### CLIENT SITE REPAIR DONE CASE ###
            elif repair.clientsite:

                # go through lines of the OR, and do moves from tech loc to client loc for pieces to add,
                # and from client loc to tech loc for pieces to remove.
                
                tech_loc_id = l_obj.search([('tech', 'ilike', self.tech.name)])
                if not tech_loc_id : 
                    raise UserError("Un problème est survenu lors de la recherche de l'emplacement associé au technicien")

                customer_loc_id = loc_obj.search(cr, uid, [('complete_name', 'ilike','Customers')])
                print "loc_client_id : %s" % loc_client_id
                
                for op_line in repair.operations : 
                    orig_loc_id = tech_loc_id
                    dest_loc_id = customer_loc_id
                    if op_line.type == 'remove':
                        orig_loc_id = customer_loc_id
                        dest_loc_id = self.location_id
                    move_id = move_obj.create(cr, uid, {
                        'origin': repair.name,
                        'name': op_line.name,
                        'product_uom': op_line.product_id.uom_id.id,
                        'product_id': op_line.product_id.id,
                        'product_uom_qty': abs(op_line.product_uom_qty),

                        'location_id': op_orig_loc_id.id, # line location
                        'location_dest_id': dest_loc_id.id, #line location

                        'restrict_lot_id': line.lot_id.id,
                    })
                    # make them done
                    move_obj.action_done(cr, uid, move_id)

        return res

class StockQuants(models.Model):

    _inherit = 'stock.quant'

    # holds the stock location the quant came form initially
    # useful only in the context of repairs, so we can trace where the piece came from,
    # and check it against the company_id of the Customer it was used for.
    origin = fields.Many2one('stock.location')


