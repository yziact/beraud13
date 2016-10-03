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


class MrpRepairInh(models.Model):
    _inherit = 'mrp.repair'

    def _set_default_end_date(self):
        return (datetime.datetime.now()+datetime.timedelta(days=1)).strftime(DATETIME_FORMAT)

    # not visible to the model until created, but exists in db
    create_date = fields.Datetime('Create Date', readonly=True)

    date_start = fields.Datetime(string='Date de début', required=True, store=True,
                                 default=fields.Datetime.now, help="Date du début de la réparation")

    end_date = fields.Datetime(string="Date de fin", store=True, help="Date prévue de la fin de la réparation",
                              default=_set_default_end_date)

    invoice_method = fields.Selection(default='after_repair')
    clientsite = fields.Boolean(string="Réparation sur Site Client : ", default=False)

    tech = fields.Many2one('res.users', string="Technicien", domain=[('company_id','in',[1,3])], company_dependent=False) 
    #tech2 = fields.Many2many('res.users', compute='_compute_techs', string='Les Techs', store=False)

    #tasks_ids = fields.Many2many('project.task', compute='_compute_tasks_ids', string='Tasks associated to this sale')
    #tech = fields.Many2one('res.users', string="Technicien", company_dependent=False) 

    #operations = fields.one2many('mrp.repair.line', 'repair_id', 'Operation Lines', readonly=True, states={'draft': [('readonly', False)]}, copy=True),
    operations = fields.One2many('mrp.repair.line', 'repair_id', 'Operation Lines', readonly=False, copy=True)

    #@api.onchange('tech2') 
    #def tech2_changed(self):
    #    self._compute_techs()
        
    @api.multi
    def _compute_techs(self):
        print "***in compute techs."
        #superself = self.sudo()
        #tech_ids = superself.env['res.users'].search([('name', 'ilike', 'Isabelle Graillat')])
        #import pdb; pdb.set_trace();
        #tech_ids = self.env['res.users'].sudo().search([('name', 'ilike', 'Isabelle Graillat')])
        #tech_ids = self.env['res.users'].sudo().search([])
        #print "tech_ids : %s" % tech_ids

        #repair.tech2 = self.env['project.task'].search([('sale_line_id', 'in', order.order_line.ids)])
        #self.tech2 = tech_ids

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
        loc_obj = self.env['stock.location'].sudo()
        tech_loc_id = loc_obj.search([('tech', 'ilike', self.tech.name)])
        print tech_loc_id.id

        all_locs_recs = loc_obj.search([]).sudo()
        all_locs_objs = []
        for r in all_locs_recs :
            all_locs_objs.append(loc_obj.browse(r.id))
            print r.tech.name

        if not tech_loc_id:
            raise UserError("Le Technicien spécifié n'a pas d'emplacement de stock assigné")

        return tech_loc_id.id

    def _set_dest_lines_to_tech(self):

        mrp_repair_line_obj = self.env['mrp.repair.line']
        loc_obj = self.env["stock.location"].sudo()
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
        if rec.clientsite:
            rec._set_dest_lines_to_tech()
        return rec

    @api.multi
    def write(self, vals):
        res = super(MrpRepairInh, self).write(vals)
        if self.clientsite:
            self._set_dest_lines_to_tech()
        return res

    def action_confirm(self, cr, uid, ids, context):

        # need to call this first for the serial ids checks
        # but this doesn't make any moves
        res = super(MrpRepairInh, self).action_confirm(cr, uid, ids, context)

        sp_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        loc_obj = self.pool.get("stock.location")
        move_list = []

        for repair in self.browse(cr, uid, ids, context={}) :

### BERAUD SITE REPAIR CONFIRM CASE ###
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
                    'move_type': 'direct',
                    'location_id': repair.location_id.id, 
                    'location_dest_id': repair.location_dest_id.id,
                })
                if picking_id:
                    sp_obj.action_confirm(cr, uid, [picking_id], context=context)
                else:
                    raise UserError("Something went wrong while creating/confirming stock_picking")

                print "picking created : %s" % sp_obj.browse(cr, uid, picking_id, context={}).name

                # add article to repair itself to the picking (we'll receive it to repair it)
                move_id = move_obj.create(cr, uid, {
                    'origin': repair.name,
                    #'name': repair.name,
                    'name': repair.product_id.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_id.uom_id.id,
                    'product_uom_qty': abs(repair.product_qty),
                    'picking_id': picking_id,
                    'picking_type_id': picking_type[0],
                    #'state': 'draft',
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                    'restrict_lot_id': repair.lot_id.id,
                }, context={})
                # don't make the move done or it won't appear in the picking...
                #move_obj.action_done(cr, uid, move_id)
                #sp_obj.write(cr, uid, picking_id, {'move_lines':[(4,move_id)]} )

                # make the moves but don't add them to the picking
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

### CLIENT SITE REPAIR CONFIRM CASE ###
            elif repair.clientsite:

                if not repair.tech:
                    raise UserError("Technicien non-spécifié")

                # get stock location corresponding to technician
                src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
                print "tech_name : %s" % repair.tech.name
                print "src_loc : %s" % src_loc
                #tech_loc_id = loc_obj.search(cr, uid, [('tech', 'ilike', repair.tech.name)])
                tech_loc_id = repair.sudo().env['stock.location'].search([('tech', 'ilike', repair.tech.name)])
                print "tech_loc_id : %s" % tech_loc_id
                print "tech_loc_id[0] : %s" % tech_loc_id[0]
                #print "repair.tech_loc_id : %s" % repair.tech_loc_id

                if not tech_loc_id:
                    raise UserError("Le Technicien spécifié n'a pas d'emplacement de stock assigné")

                tech_loc = repair.sudo().env['stock.location'].browse(tech_loc_id[0].id) 
                print tech_loc.name

                repair._set_dest_lines_to_tech()

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
        
        print "Mrp_repair action_done"
        res = {}
        move_obj = self.pool.get('stock.move')
        repair_line_obj = self.pool.get('mrp.repair.line')
        loc_obj = self.pool.get("stock.location")
        sp_obj = self.pool.get('stock.picking')

        for repair in self.browse(cr, uid, ids, context=context):
### BERAUD SITE REPAIR DONE CASE ###
            if not repair.clientsite:

                # create move for each repair_line, and set it to done
                # each repair line will go to where it was supposed to.
                # No need to create BL/BR for them
                move_ids = []
                for line in repair.operations:
                    print "processing line : %s" % line.name
                    move_id = move_obj.create(cr, uid, {
                        'origin': repair.name,
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'restrict_lot_id': line.lot_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'partner_id': repair.address_id and repair.address_id.id or False,
                        'location_id': line.location_id.id,
                        'location_dest_id': line.location_dest_id.id,
                    })
                    print 'appending'
                    move_ids.append(move_id)
                    #move_obj.action_done(cr, uid, move_id)
                    # set repair line to done
                    print 'setting repair line to done'
                    repair_line_obj.write(cr, uid, [line.id], {
                        'move_id': move_id, 
                        'state': 'done'
                    }, context=context)
                    print 'looping back'

                print "we're here"
                # set all line moves to done

                src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
                wh = loc_obj.get_warehouse(cr, uid, src_loc, context={})
                print "SRC LOC : %s" % src_loc
                print "WH : %s" % src_loc

                picking_type = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'outgoing'), ('warehouse_id', '=', wh)])
                print "picking type : %s" % picking_type

                if not picking_type:
                    raise UserError("Something went wrong while selecting the picking type.")

                # Create picking (BL)
                # We'll deliver the article after having it fixed
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

                # adding repaired product to BL
                move_id = move_obj.create(cr, uid, {
                    'name': repair.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                    'product_uom_qty': repair.product_qty,
                    'partner_id': repair.address_id and repair.address_id.id or False,
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                    'picking_id': picking_id,
                    'picking_type_id': picking_type[0],
                    'restrict_lot_id': repair.lot_id.id,
                })

                move_ids.append(move_id)

                if not move_id:
                    raise UserError("Something went wrong while creating the move for the repaired item")

                # If we set the moves to done, the BL will also be set to done, 
                # but the move lines won't appear on the BL
                #move_obj.action_done(cr, uid, move_ids, context=context) 

                # repair has ended
                self.write(cr, uid, [repair.id], {'state': 'done', 'move_id': move_id}, context={})
                res[repair.id] = move_id
                return res

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

                #move_id = move_obj.create(cr, uid, {
                    #'origin': repair.name,
                    #'name': line.name,
                    #'product_uom': line.product_id.uom_id.id,
                    #'product_id': line.product_id.id,
                    #'product_uom_qty': abs(line.product_uom_qty),
                    #'location_id': line.location_id.id, # line location
                    #'location_dest_id': tech_loc.id, #line location
                    #'restrict_lot_id': line.lot_id.id,
                #})

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

                        move_info_list.append({'origin':repair.name,
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


