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

    # task_id = fields.Many2one('project.task', string='Associated Task', domain=_task_domain)

    bl = fields.Many2one('stock.picking')
    br = fields.Many2one('stock.picking')

    task_id = fields.Many2one('project.task')

    def open_task_line(self, cr, uid, ids, context=None):
        print "open_task_like button clicked"

        for repair in self.browse(cr, uid, ids, context={}) :
            print "task_id : ", repair.task_id
            return {
                "type": "ir.actions.act_window",
                "res_model": "project.task",
                "views": [[False, "form"]],
                #"res_id": a_product_id,
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

    def _set_dest_of_lines(self, new_tech=None):
        print "_set_dest_of_lines"

        loc_obj = self.env["stock.location"]
        t_obj = self.env['res.users']
        dest_loc_id = 0
        print '[sdol]self.tech : ', self.tech
        print '[sdol]new_tech : ', new_tech

        if new_tech:
            new_tech_name = t_obj.browse(new_tech).name
            dest_loc_id = loc_obj.search([('tech', 'ilike', new_tech_name)])
            print "--> new tech, dest_loc_id : ", dest_loc_id
            if not dest_loc_id:
                raise UserError("[gslfr] Le Technicien spécifié n'a pas d'emplacement de stock assigné")
        #False means we changed from a tech to None, None means we didn't pass anything
        elif self.tech and new_tech != False: 
            dest_loc_id = loc_obj.search([('tech', 'ilike', self.tech.name)])
            print "--> tech, dest_loc_id : ", dest_loc_id
            if not dest_loc_id:
                raise UserError("[gslfr] Le Technicien spécifié n'a pas d'emplacement de stock assigné")
        else:
            dest_loc_id = loc_obj.search([('complete_name','ilike','Virtual Locations/Production')])
            print "--> NO TECH, dest_loc_id : ", dest_loc_id
            if not dest_loc_id:
                raise UserError("[gslfr] Emplacement Virtuel de Production non trouvé.")

        rebut_loc_id = loc_obj.search([('complete_name','ilike','Virtual Locations/Scrapped')])
        for line in self.operations:
            print "updating lines with location : %s" % dest_loc_id.name
            if line.type == 'add':
                line.write({ 'location_dest_id':dest_loc_id.id })
            else:
                line.write({ 'location_dest_id':rebut_loc_id.id })

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
        rebut_loc_id = l_obj.search([('complete_name','ilike','Virtual Locations/Scrapped')])

        c_id = partner_obj.browse(vals['partner_id']).company_id.id
        print "c_id : ", c_id

        if c_id == 1:
            vals['location_id'] = ber_loc_id.id
        else:
            vals['location_id'] = atom_loc_id.id
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
                    ld_id = rebut_loc_id.id

                # if there's a tech, change the dest location
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
        rebut_loc_id = l_obj.search([('complete_name','ilike','Virtual Locations/Scrapped')])

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
                    ld_id = rebut_loc_id.id

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
            p_id = proj_obj.search(cr, uid, [('name', 'ilike', 'SAV')])
            project_id = proj_obj.browse(cr, uid, p_id)

            if not project_id : 
                raise UserError("Aucun projet 'SAV' trouvé.")

            task_id = task_obj.create(cr, uid, {
                'project_id' : project_id.id,
                'name' : repair.name,
                'partner_id' : repair.partner_id.id,
            })
            
            print "task créée, id : ", task_id
            repair.task_id = task_id

### BERAUD SITE REPAIR CONFIRM CASE ###
            if not repair.clientsite:
                # the picking type is always incoming, but depends on the warehouse it comes from...
                # this will determine the sequence of the generated stock picking
                src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
                wh = loc_obj.get_warehouse(cr, uid, src_loc, context={})
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
                # confirm does that right ?

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

                ### MOVES FOR LINES 
                # make the moves but don't add them to the picking
                # moves lines to the location they need to be for the repair
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

                ### Create picking BL
                # we create in in draft mode (default)
                # We'll deliver the article after having it fixed
                # Create move corresponding to repaired article, added to the picking

                picking_id = sp_obj.create(cr, uid, {
                    'origin':repair.name,
                    'product_id': repair.product_id,
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
                src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
                print "tech_name : %s" % repair.tech.name
                print "src_loc : %s" % src_loc
                #tech_loc_id = loc_obj.search(cr, uid, [('tech', 'ilike', repair.tech.name)])
                tech_loc_id = repair.env['stock.location'].search([('tech', 'ilike', repair.tech.name)])
                print "tech_loc_id : %s" % tech_loc_id
                print "tech_loc_id[0] : %s" % tech_loc_id[0]
                #print "repair.tech_loc_id : %s" % repair.tech_loc_id

                if not tech_loc_id:
                    raise UserError("Le Technicien spécifié n'a pas d'emplacement de stock assigné")

                tech_loc = repair.env['stock.location'].browse(tech_loc_id.id) 
                print tech_loc.name

                #repair._set_dest_lines_to_tech()

                ## create and reserve moves corresponding to the operation lines
                # The machine to repair is already at the client site, no need to do a move for it
                # We only need to move the items that will serve its repair
                # These moves are not linked to a picking at all
                # Pieces move from the stock to the techs stock location
                # Reserved 
                # The guy giving the product, will confirm the move himself.
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
                        'location_dest_id': tech_loc.id, #line location
                        'restrict_lot_id': line.lot_id.id,
                    })
                    print "Action assign start"
                    move_obj.action_assign(cr, uid, move_id)
                    move_obj.force_assign(cr, uid, move_id)
                    print "Action assign end"

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

### CLIENT SITE REPAIR DONE CASE ###
            elif repair.clientsite:

                # fetch all moves corresponding to our current repair
                move_ids = move_obj.search(cr, uid, [('origin', 'ilike', repair.name)])
                print "moves corresponding to the repair are : %s" % move_ids
                # move_ids ex : [5811, 5812]

                # get the client stock location
                loc_client_id = loc_obj.search(cr, uid, [('complete_name', 'ilike','Customers')])
                print "loc_client_id : %s" % loc_client_id

                if not loc_client_id:
                    raise UserError("Something went wrong while getting the client location in stock")

                loc_client_obj = loc_obj.browse(cr, uid, loc_client_id[0])
                print "Client Location name : %s" % loc_client_obj.complete_name

                # Unreserve moves and make them 'done'
                move_info_list = []
                for move_id in move_ids:
                    move = move_obj.browse(cr, uid, move_id)
                    if move.state == 'assigned':
                        print "setting move %s that was reserved to unreserved" % move_id
                        #move_obj.write(cr, uid, move_id, {'state': 'done'})
                        move_obj.do_unreserve(cr, uid, move_id, context={})
                        print "setting move %s that was unreserved to done" % move_id
                        move_obj.action_done(cr, uid, move_id, context={})
                        print "moves %s restrict_lot_id : %s" % (move_id, move.restrict_lot_id)
                        print "next move will have location id : %s" % move.location_dest_id
                        print "move.restrict_lot_id : %s" % move.restrict_lot_id

                        move_info_list.append({
                            'origin':repair.name,
                            'name':move.name,
                            'product_id':move.product_id.id,
                            'product_uom':move.product_id.uom_id.id,
                            'product_uom_qty': move.product_uom_qty,
                            'location_id':move.location_dest_id.id, # should be tech location
                            'location_dest_id':loc_client_obj.id, # is client stock location
                            'restrict_lot_id': move.restrict_lot_id.id,
                        })
                    else:
                        print "move %s was already done before the end of this repair." % move_id

                # once moves are done from the Stock to the Technician, we'll have to create new moves
                # from the technician to the Client stock location
                # make move with product_id AND restrict_lot_id
                # and set them to done
                move_list=[]
                for mi in move_info_list:
                    move_id = move_obj.create( cr, uid, {
                        'origin': mi['origin'],
                        'name': mi['name'],
                        'product_uom': mi['product_uom'],
                        'product_id': mi['product_id'],
                        'product_uom_qty': mi['product_uom_qty'],
                        'location_id': mi['location_id'],
                        'location_dest_id': mi['location_dest_id'],
                        'restrict_lot_id': mi['restrict_lot_id'],
                    })
                    move_obj.action_done(cr, uid, move_id, context={})
                    
        return res



