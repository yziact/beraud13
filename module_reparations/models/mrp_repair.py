# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
from utilsmod import utilsmod
from openerp.exceptions import UserError

import logging 
_logger = logging.getLogger(__name__)

class MrpRepairInh(models.Model):
    _inherit = 'mrp.repair'

    # not visible to the model until created, but exists in db
    create_date = fields.Datetime('Create Date', readonly=True)

    date_start = fields.Datetime(string='Date de début', required=True, store=True, index=True, copy=False, default=fields.Datetime.now, help="Date du début de la réparation")
    end_date = fields.Datetime(string="Date de fin", store=True, help="Date prévue de la fin de la réparation")

    invoice_method = fields.Selection(default='after_repair')
    clientsite = fields.Boolean(string="Réparation sur Site Client : ", default=False)
    
    tech = fields.Many2one('res.users', string="Technicien") 

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        mask = utilsmod.ReportMask(['module_reparations.report_repair_devis',
                                    'module_reparations.report_no_prices'])
        res = super(MrpRepairInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(res, self)

    @api.onchange('tech') 
    def tech_change(self):
        print "tech has changed !"
        if not self.tech:
            return
        else:
            self._set_dest_lines_to_tech()

    def _get_stock_loc_from_tech(self):

        print "get stock loc from tech"
        # get stock location corresponding to technician
        # src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
        print self.tech.name
        loc_obj = self.env['stock.location']
        tech_loc_id = loc_obj.search([('tech', 'ilike', self.tech.name)])
        print tech_loc_id.id

        if not tech_loc_id:
            raise UserError("Le Technicien spécifié n'a pas d'emplacement de stock assigné")

        return tech_loc_id.id

    def _set_dest_lines_to_tech(self):

        mrp_repair_line_obj = self.env['mrp.repair.line']
        loc_obj = self.env["stock.location"]
        tech_loc_id = self._get_stock_loc_from_tech()

        if not self.tech:
            return

        tech_loc = loc_obj.browse(tech_loc_id) 

        for line in self.operations:
            print "updating lines with location : %s" % tech_loc.name
            line.write({ 'location_dest_id':tech_loc.id })

    @api.model
    def create(self, vals):
        rec = super(MrpRepairInh, self).create(vals)
        rec._set_dest_lines_to_tech()
        return rec

    @api.multi
    def write(self, vals):
        res = super(MrpRepairInh, self).write(vals)
        self._set_dest_lines_to_tech()
        return res

    def action_confirm(self, cr, uid, ids, context):

        # need to call this first for the serial ids checks
        res = super(MrpRepairInh, self).action_confirm(cr, uid, ids, context)

        sp_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        loc_obj = self.pool.get("stock.location")
        move_list = []

        for repair in self.browse(cr, uid, ids, context={}) :
            print "clientsite : %s" % repair.clientsite

### BERAUD REPAIR CASE ###
            if not repair.clientsite:
                # the picking type is always incoming, but depends on the warehouse it comes from...
                # this will determine the sequence of the generated stock picking
                src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
                wh = loc_obj.get_warehouse(cr, uid, src_loc, context={})
                print "SRC LOC : %s" % src_loc
                print "WH : %s" % src_loc

                picking_type = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', wh)])
                print "picking type : %s" % picking_type

                if not picking_type:
                    raise UserError("Something went wrong while selecting the picking type.")

                # Create picking
                picking_id = sp_obj.create(cr, uid, {
                    'origin':repair.name,
                    'partner_id': repair.partner_id.id, 
                    'picking_type_id': picking_type[0],
                    'location_id': repair.location_id.id, 
                    'location_dest_id': repair.location_dest_id.id,
                })
                if picking_id:
                    sp_obj.action_confirm(cr, uid, [picking_id], context=context)
                else:
                    raise UserError("Something went wrong while creating/confirming stock_picking")

                print "picking created : %s" % sp_obj.browse(cr, uid, picking_id, context={}).name

                # add article to repair itself to the picking (we'll receive it to repair it)
                move_list.append(move_obj.create(cr, uid, {
                    'origin': repair.name,
                    'name': repair.name,
                    'product_uom': repair.product_id.uom_id.id,
                    'picking_id': picking_id,
                    'picking_type_id': picking_type[0],
                    'product_id': repair.product_id.id,
                    'product_uom_qty': abs(repair.product_qty),
                    #'state': 'draft',
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                }, context={}))

                # add operation lines to the picking
                for line in repair.operations:
                    print "creating move : %s" % line.name
                    # add move lines to the picking
                    move_list.append(move_obj.create(cr, uid, {
                        'origin': repair.name,
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': picking_id,
                        'picking_type_id': picking_type[0], 
                        'product_id': line.product_id.id,
                        'product_uom_qty': abs(line.product_uom_qty),
                        #'state': 'draft',
                        'location_id': line.location_id.id, # line location
                        'location_dest_id': line.location_dest_id.id, #line location
                    }, context={}))

### CLIENT REPAIR CASE ###
            elif repair.clientsite:
                if not repair.tech:
                    raise UserError("Technicien non-spécifié")

                # get stock location corresponding to technician
                #src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
                print repair.tech.name
                tech_loc_id = loc_obj.search(cr, uid, [('tech', 'ilike', repair.tech.name)])
                print tech_loc_id

                if not tech_loc_id:
                    raise UserError("Le Technicien spécifié n'a pas d'emplacement de stock assigné")

                tech_loc = loc_obj.browse(cr, uid, tech_loc_id[0], context={}) 
                print tech_loc.name

                repair._set_dest_lines_to_tech()

                # no pickings to generate, but stock moves to be created and reserved
                # from the technician's vehicle stock location
                # add article to repair itself to the picking (we'll receive it to repair it)
                # reserve move from STOCK to technician's car.
                # The guy giving the product, will confirm the move himself.
                move_list.append(move_obj.create(cr, uid, {
                    'origin': repair.name,
                    'name': repair.name,
                    'product_uom': repair.product_id.uom_id.id,
                    #'picking_type_id': picking_type[0],
                    'product_id': repair.product_id.id,
                    'state': 'assigned', # maybe that works, maybe it doesn't
                    'product_uom_qty': abs(repair.product_qty),
                    'location_id': repair.location_id.id,
                    'location_dest_id': tech_loc.id,
                }, context={}))

                ## create and reserve moves corresponding to the operation lines
                for line in repair.operations:
                    print "creating move : %s" % line.name
                    # add move lines to the picking
                    move_list.append(move_obj.create(cr, uid, {
                        'origin': repair.name,
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        #'picking_type_id': picking_type[0], 
                        'product_id': line.product_id.id,
                        'product_uom_qty': abs(line.product_uom_qty),
                        'state': 'assigned',
                        'location_id': line.location_id.id, # line location
                        'location_dest_id': tech_loc.id, #line location
                    }, context={}))

        return res

    #@api.multi
    #def write(self, vals):
        #write_res = super(Users, self).write(vals)
        #if vals.get('groups_id'):
            ## form: {'group_ids': [(3, 10), (3, 3), (4, 10), (4, 3)]} or {'group_ids': [(6, 0, [ids]}
            #user_group_ids = [command[1] for command in vals['groups_id'] if command[0] == 4]
            #user_group_ids += [id for command in vals['groups_id'] if command[0] == 6 for id in command[2]]
            #self.env['mail.channel'].search([('group_ids', 'in', user_group_ids)])._subscribe_users()
        #return write_res

    def action_repair_done(self, cr, uid, ids, context=None):
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
        
        print "our action_done"
        res = {}
        move_obj = self.pool.get('stock.move')
        repair_line_obj = self.pool.get('mrp.repair.line')
        loc_obj = self.pool.get("stock.location")
        sp_obj = self.pool.get('stock.picking')

        for repair in self.browse(cr, uid, ids, context=context):
            print "clientsite : %s" % repair.clientsite
            move_ids = []
            # create move for each repair_line
            for move in repair.operations:
                move_id = move_obj.create(cr, uid, {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'restrict_lot_id': move.lot_id.id,
                    'product_uom_qty': move.product_uom_qty,
                    'product_uom': move.product_uom.id,
                    'partner_id': repair.address_id and repair.address_id.id or False,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })
                move_ids.append(move_id)
                repair_line_obj.write(cr, uid, [move.id], {
                    'move_id': move_id, 
                    'state': 'done'
                }, context=context)

            move_id = None
            if not repair.clientsite:
                src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
                wh = loc_obj.get_warehouse(cr, uid, src_loc, context={})
                print "SRC LOC : %s" % src_loc
                print "WH : %s" % src_loc

                picking_type = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'outgoing'), ('warehouse_id', '=', wh)])
                print "picking type : %s" % picking_type

                if not picking_type:
                    raise UserError("Something went wrong while selecting the picking type.")

                # Create picking
                # Create move corresponding to repaired article, added to the picking
                picking_id = sp_obj.create(cr, uid, {
                    'origin':repair.name,
                    'product_id': repair.product_id,
                    'partner_id': repair.partner_id.id, 
                    'picking_type_id': picking_type[0],
                    'location_id': repair.location_id.id, 
                    'location_dest_id': repair.location_dest_id.id,
                })
                if picking_id:
                    sp_obj.action_confirm(cr, uid, [picking_id], context=context)
                else:
                    raise UserError("Something went wrong while creating/confirming stock_picking")

                move_id = move_obj.create(cr, uid, {
                    'name': repair.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                    'product_uom_qty': repair.product_qty,
                    'partner_id': repair.address_id and repair.address_id.id or False,
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                    'restrict_lot_id': repair.lot_id.id,
                    'picking_id': picking_id,
                    'picking_type_id': picking_type[0],
                })
            elif repair.clientsite:
                move_id = move_obj.create(cr, uid, {
                    'name': repair.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                    'product_uom_qty': repair.product_qty,
                    'partner_id': repair.address_id and repair.address_id.id or False,
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                    'restrict_lot_id': repair.lot_id.id,
                })

            #move_ids.append(move_id)
            #move_obj.action_done(cr, uid, move_ids, context=context)
            if move_id == None:
                raise UserError("Something went wrong while create the move for the repaired item")

            self.write(cr, uid, [repair.id], {'state': 'done', 'move_id': move_id}, context={})
            res[repair.id] = move_id
            return res

