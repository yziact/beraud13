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

no_tech_loc_error_default = "Tech has no assigned locations, field filled with default values"

class MrpRepairInh(models.Model):
    _inherit = 'mrp.repair'


    def get_dict_time(self):
        # cette fonction à pour but de creer un dictionnaire regroupant les lines de temps par tache/incident commun
        # les clefs de ce dictionnaire sont elles meme des records
        list_time = self.task_id.timesheet_ids

        values = set(map(lambda x: x.issue_id or x.task_id, list_time))
        newdict = {}

        for parent in values:
            print parent
            newdict[parent] = []
            print newdict
            for time_line in list_time:
                if time_line.issue_id == parent or time_line.task_id == parent:
                    newdict[parent].append(time_line)

        print newdict
        return newdict

    @api.multi
    def action_repair_sign(self):
        for repair in self:
            repair.write({'state': 'to_sign'})
            repair.task_id.repair_state = True

    def action_repair_start(self, cr, uid, ids, context=None):
        for repair in self.browse(cr, uid, ids, context={}):
            repair.task_id.repair_state = False

        res = super(MrpRepairInh, self).action_repair_start(cr, uid, ids, context=context)

        return res


    def _set_default_end_date(self):
        return (datetime.datetime.now()+datetime.timedelta(days=1)).strftime(DATETIME_FORMAT)

    def _set_default_location(self):
        loc_id = self.env['stock.location'].search([('complete_name','ilike','Emplacements physiques/DC/REP')])
        return loc_id

    def _set_default_dest_location(self):
        loc_id = self.env['stock.location'].search([('complete_name','ilike','Partner Locations/Customers')])
        return loc_id

    ### commercial system

    def onchange_partner_id(self, cr, uid, ids, part, address_id):
        res = super(MrpRepairInh, self).onchange_partner_id(cr, uid, ids, part, address_id)
        part_env = self.pool.get('res.partner')
        if not part:
            return res

        partner = part_env.browse(cr, uid, part)
        if partner.user_id:
            user_id = partner.user_id.id
            res['value']['user_id'] = user_id
        return res

    def _default_commercial(self):
        print "OUR DEFAULT COMMERCIAL"
        print self.env.context
        print self.env.user

        if not self.contact_affaire:
            return self.env.user

    contact_affaire = fields.Many2one('res.users', string='V/Contact affaire', default=_default_commercial)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    ####

    client_order_ref = fields.Char('Customer Reference', size=64)
    # add contact
    contact = fields.Many2one('res.partner', readonly=True, states={'draft': [('readonly', False)]})


    # override workflow states
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('valid', u'Bon de Commande'),
        ('confirmed', 'Confirmed'),
        ('ready', 'Ready to Repair'),
        ('to_sign', 'A Signer'),
        ('under_repair', 'Under Repair'),
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
                                       default=_set_default_dest_location)

    # bl and br for beraud site repairs
    bl = fields.Many2one('stock.picking')
    br = fields.Many2one('stock.picking')

    # internal bl, from stock to tech stock, for client site repairs
    bl_internal = fields.Many2one('stock.picking')

    # task associated to 
    task_id = fields.Many2one('project.task')

    # moves generated linked to our OR
    linked_moves = fields.Many2many('stock.move')

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

    def open_bl(self, cr, uid, ids, context=None):
        print "open_picking button clicked"

        for repair in self.browse(cr, uid, ids, context={}) :
            print "br_id : ", repair.br
            print "bl_id : ", repair.bl
            print "repair_id", repair.id

            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "views": [[False, "tree"], [False, "form"]],
                "domain": [['repair_id', '=', repair.id]],
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
        error = 0
        for line in self.operations:
            error += line.update_line();
        if error :
            return { 'warning': {'title': 'Attention', 'message': no_tech_loc_error_default} }


    def action_repair_validate(self, cr, uid, ids, context=None):
        print "mrp_repair our action_validate"
        for repair in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [repair.id], {'state': 'valid'}, context=context)

    @api.model
    def create(self, vals):
        print "***mrp repair our create"


        ### set location_id/dest_id of repair
        if not vals['partner_id']:
            print "partner_id empty in vals in create"
            raise UserError("Il faut un partenaire pour sélectionner les emplacements source/destination")

        partner_obj = self.env['res.partner']
        p_obj = self.env['product.product']
        t_obj = self.env['res.users']
        l_obj = self.env['stock.location']

        rep_ber_loc_id = self.env['stock.location'].search([('complete_name','ilike','Emplacements physiques/DC/REP')])
        rep_atom_loc_id = self.env['stock.location'].search([('complete_name','ilike','Emplacements physiques/DAT/REP')])

        ber_loc_id = l_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        atom_loc_id = l_obj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        customer_loc_id = l_obj.search([('complete_name','ilike','Partner Locations/Customers')])

        production_loc_id = l_obj.search([('complete_name','ilike','Virtual Locations/Production')])
        remove_loc_id = l_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])

        c_id = partner_obj.browse(vals['partner_id']).company_id.id
        print "c_id : ", c_id

        #vals['location_id'] = ber_loc_id.id
        vals['location_id'] = rep_ber_loc_id.id
        remove_loc_id = ber_loc_id

        stock_loc_id = ber_loc_id
        if c_id == 3:
            stock_loc_id = atom_loc_id
            vals['location_id'] = rep_atom_loc_id.id
            remove_loc_id = atom_loc_id

        vals['location_dest_id'] = customer_loc_id.id

        ### set location_id/dest_id of repair_lines
        p_obj = self.env['product.product']
        t_obj = self.env['res.users']
        l_obj = self.env['stock.location']

        if vals.get('operations', False):
            for v in vals['operations']:
                o = v[2]
                print "o was : ", o
                #l_id = vals['location_id'] # product is taken from the stock set in the repair
                if o.get('type') == 'add':
                    l_id = stock_loc_id.id
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
        rec = super(MrpRepairInh, self).write(vals)
        #self._set_dest_of_lines(vals.get('tech'))
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
        repair_obj = self.pool.get('mrp.repair')
        move_list = []

        for repair in self.browse(cr, uid, ids, context={}) :
            print repair.id

            # create the task in project 'SAV'
            proj_name = 'REPARATIONS ATELIER'
            user = uid
            if repair.clientsite :
                proj_name = 'SAV'

                if repair.tech:
                    user = repair.tech.id

            p_id = proj_obj.search(cr, uid, [('name', 'ilike', proj_name)])
            project_id = proj_obj.browse(cr, uid, p_id)

            if not project_id :
                raise UserError("Aucun projet '%s' trouvé." % proj_name)

            task_id = task_obj.create(cr, uid, {
                'project_id' : project_id.id,
                'name' : repair.name,
                'partner_id' : repair.partner_id.id,
                'user_id' : user,
            })

            print "task créée, id : ", task_id
            repair.task_id = task_id

            src_loc = loc_obj.browse(cr, uid, repair.location_id.id, context=context)
            wh = loc_obj.get_warehouse(cr, 1, src_loc, context={})

            v_loc_id = loc_obj.search(cr, uid, [('complete_name', 'ilike','Partner Locations/Vendors')])
            vendeur_loc_id = loc_obj.browse(cr, uid, v_loc_id)
            ### BERAUD SITE REPAIR CONFIRM CASE ###
            if not repair.clientsite:
                # the picking type is always incoming, but depends on the warehouse it comes from...
                # this will determine the sequence of the generated stock picking
                print "SRC LOC : %s" % src_loc
                print "WH : %s" % wh

                picking_type_in_id = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', wh), ('name','ilike','SAV')])
                picking_type_in = self.pool.get('stock.picking.type').browse(cr, uid, [picking_type_in_id[0]])

                picking_type_out_id = self.pool.get('stock.picking.type').search(
                    cr, uid, [('code', '=', 'outgoing'), ('warehouse_id', '=', wh), ('name','ilike','SAV')])
                picking_type_out = self.pool.get('stock.picking.type').browse(cr, uid, [picking_type_out_id[0]])

                print "picking_type_in : %s" % picking_type_in
                print "picking_type_in.name : %s" % picking_type_in.name
                print "picking_type_out : %s" % picking_type_out
                print "picking_type_out.name : %s" % picking_type_out.name

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
                    'picking_type_id': picking_type_in.id,
                    'move_type': 'direct',
                    #'location_id': repair.location_dest_id.id, # comes from the client location
                    'location_id': vendeur_loc_id.id, # comes from the client location
                    'location_dest_id': repair.location_id.id, # to our location
                    'repair_id': repair.id,
                })

                # add article to repair to the picking (we'll receive it to repair it)
                move_id = move_obj.create(cr, uid, {
                    'origin': repair.name,
                    'name': repair.product_id.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_id.uom_id.id,
                    'product_uom_qty': repair.product_qty,
                    'picking_id': picking_id,
                    'picking_type_id': picking_type_in.id,
                    #'state': 'draft',
                    #'location_id': repair.location_dest_id.id, # client location to
                    'location_id': vendeur_loc_id.id, # client location to
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
                    'partner_id': repair.address_id and repair.address_id.id or repair.partner_id.id,
                    'picking_type_id': picking_type_out.id,
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                    'repair_id': repair.id,
                })

                # adding repaired product to BL
                move_id = move_obj.create(cr, uid, {
                    'origin':repair.name,
                    'name': repair.product_id.name,
                    'product_id': repair.product_id.id,
                    'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                    'product_uom_qty': repair.product_qty,
                    'partner_id': repair.address_id and repair.address_id.id or repair.partner_id.id,
                    'location_id': repair.location_id.id,
                    'location_dest_id': repair.location_dest_id.id,
                    'picking_id': picking_id,
                    'picking_type_id': picking_type_out.id,
                    'restrict_lot_id': repair.lot_id.id,
                })

                if not move_id:
                    raise UserError("Something went wrong while creating move for BL")

                print "to bl"
                repair.bl = picking_id
                print "BL created : %s" % sp_obj.browse(cr, uid, picking_id, context={}).name

                ### create moves corresponding to repair lines and _reserve_ them
                # do this even for the lines that are in 'delete' mode. So add and delete, same move.
                print "*** ACTION_CONFIRM, CREATING MOVES CORRESPONDING TO OPERATIONS : "
                for line in repair.operations :
                    move_id = move_obj.create(cr, uid, {
                        'origin': repair.name,
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'location_id': line.location_id.id, # line location
                        'location_dest_id': line.location_dest_id.id, #line location
                        'restrict_lot_id': line.lot_id.id,
                    })
                    move_obj.action_confirm(cr, uid, move_id)
                    move_obj.action_assign(cr, uid, move_id)
                    print "created move, move_id : ", move_id
                    line.associated_move = move_id
                    repair_obj.write(cr, uid, [repair.id], {'linked_moves' : [(4, move_id)]} )

                print "*** LINKED MOVES : ", repair.linked_moves

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

                # create BL Internal only if there are lines in the OR
                s_loc_id = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DC/Stock')])
                if repair.sudo().partner_id.company_id.id == 3:
                    s_loc_id = loc_obj.search(cr, uid, [('complete_name','ilike','Physical Locations/DAT/Stock')])
                stock_loc_id = loc_obj.browse(cr, uid, s_loc_id)

                if repair.operations :
                    picking_id = sp_obj.create(cr, uid, {
                        'origin':repair.name,
                        'product_id': repair.product_id.id,
                        'partner_id': repair.partner_id.id,
                        'picking_type_id': picking_type_internal[0],
                        'location_id': stock_loc_id.id,
                        'location_dest_id': tech_loc_id.id,
                    })

                    for line in repair.operations:
                        print "creating move : %s" % line.name
                        # add move lines to the picking
                        if line.type != 'add':
                            continue
                        move_id = move_obj.create(cr, uid, {
                            'origin': repair.name,
                            'name': line.name,
                            'product_uom': line.product_id.uom_id.id,
                            'product_id': line.product_id.id,
                            #'product_uom_qty': abs(line.product_uom_qty),
                            'product_uom_qty': line.product_uom_qty,
                            'picking_id': picking_id,
                            'picking_type_id': picking_type_internal[0],
                            'location_id': line.location_id.id, # line location
                            'location_dest_id': line.location_dest_id.id, #line location
                            'restrict_lot_id': line.lot_id.id,
                        })
                        if not move_id:
                            raise UserError("Problème survenu lors de la création du BL interne vers le technicien")
                        m = move_obj.browse(cr, uid, move_id)

                    # quants don't exist yet cause the moves (and the BL) are in draft state.
                    # quants will be created only when the move gets confirmed
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
        quants_obj = self.pool.get('stock.quant')

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

                # take moves from linked_moves, and make them done.
                print "linked_moves : ", repair.linked_moves
                for move in repair.linked_moves :
                    move_obj.action_assign(cr,uid, move.id)

                    if move.state != 'assigned':
                        raise UserError(u"Il n'y a pas de stock réservable pour la pièce %s" % move.product_id.name)
                    move_obj.action_done(cr, uid, move.id)

                ### CLIENT SITE REPAIR DONE CASE ###
            elif repair.clientsite:
                # if the internal BL to the tech is not yet "done", we can't finish the repair.
                if repair.bl_internal and repair.bl_internal.state != 'done' :
                    raise UserError("""Le bon de livraison interne Stock -> Technicien n'est pas dans l'état 'fini',
                                    impossible de terminer la réparation sans cela.""")

                # go through lines of the OR, and do moves from tech loc to client loc for pieces to add,
                # and from client loc to tech loc for pieces to remove.

                c_loc_id = loc_obj.search(cr, uid, [('complete_name', 'ilike','Customers')])
                customer_loc_id = loc_obj.browse(cr, uid, c_loc_id)
                print "customer_loc_id : %s" % customer_loc_id

                #r_loc_id = loc_obj.search(cr, uid, [('complete_name', 'ilike','Physical Locations/DC/Stock')])
                #if repair.partner_id.company_id.id == 3:
                #r_loc_id = loc_obj.search(cr, uid, [('complete_name', 'ilike','Physical Locations/DAT/Stock')])
                #remove_loc_id = loc_obj.browse(cr, uid, r_loc_id)

                t_loc_id = loc_obj.search(cr, uid, [('tech', 'ilike', repair.tech.name)])
                tech_loc_id = loc_obj.browse(cr, uid, t_loc_id)
                if not tech_loc_id :
                    raise UserError("Un problème est survenu lors de la recherche de l'emplacement associé au technicien")

                processed_moves = []
                for op_line in repair.operations :
                    print "=========////////=========////////// looping in op_line : ", op_line.product_id.name
                    orig_loc_id = tech_loc_id
                    dest_loc_id = customer_loc_id
                    if op_line.type == 'remove':
                        orig_loc_id = customer_loc_id
                        dest_loc_id = tech_loc_id

                    t_quants = quants_obj.search(cr, uid, [
                        ('location_id.id', '=', tech_loc_id.id),
                        ('product_id', '=', op_line.product_id.id)])
                    tech_quants = quants_obj.browse(cr, uid, t_quants)
                    qty_quants = sum([q.qty for q in tech_quants])
                    print 'tech_quants : ', tech_quants
                    print 'tech_quants.id : ', tech_quants.ids
                    print 'qty_quants : ', qty_quants

                    # the move will be considered a sale if
                    # the tech has the product in his stock
                    # and the quant.origin of the move in the
                    # the BL_internal to his stock
                    # is different than the company_id of the customer he used the product for.

                    isSale = False
                    quant_company_id = repair.company_id.id
                    for quant in tech_quants :
                        quant_company_id = quant.company_id.id
                        print "quant_origin : ", quant.origin
                        print "repair.partner_id.company_id.id : ", repair.partner_id.company_id.id
                        if (quant.origin.id != repair.partner_id.company_id.id) and op_line.type == 'add':
                            isSale = True

                    # these moves should be from the technician the the client
                    move_id = move_obj.create(cr, uid, {
                        'quant_ids': [6,0,tech_quants.ids],
                        'company_id': repair.company_id.id,
                        'partner_id':repair.partner_id.id,
                        'date':repair.end_date,
                        'origin': repair.name,
                        'name': op_line.name,
                        'product_uom': op_line.product_id.uom_id.id,
                        'product_id': op_line.product_id.id,
                        'product_uom_qty': op_line.product_uom_qty,
                        'location_id': orig_loc_id.id, # line location
                        'location_dest_id': dest_loc_id.id, #line location
                        'restrict_lot_id': op_line.lot_id.id,
                        'isSale': isSale,
                    })
                    move = move_obj.browse(cr, uid, move_id)

                    # make them done
                    loc_company_id = orig_loc_id.company_id.id
                    orig_loc_id.sudo().write({'company_id':quant_company_id})


                    move.sudo().action_confirm()
                    move.sudo().action_assign()
                    if move.state != 'assigned':
                        raise UserError(u"Il n'y a pas de stock réservable pour la pièce %s" % move.product_id.name)
                    move.sudo().action_done()
                    move.sudo().write({'date':repair.end_date})
                    
                    orig_loc_id.sudo().write({'company_id':loc_company_id})

                    # move_obj.action_confirm(cr, uid, move_id)
                    # move_obj.action_assign(cr, uid, move_id)
                    # import pudb;
                    # pudb.set_trace()
                    # move_obj.action_done(cr, uid, move_id)

                    print "move done, id : ", move_id
                    print "move was a sale ? : ", isSale

        return res

    def action_invoice_create(self, cr, uid, ids, group=False, context=None):
        print "module reparations our action_invoice_create"

        res = super(MrpRepairInh, self).action_invoice_create(cr, uid, ids, group=group, context=context)

        inv_obj = self.pool.get('account.invoice')
        team_obj = self.pool.get('crm.team')

        a_team_id = team_obj.search(cr, uid, [('code','ilike','ATOMSAV')])
        b_team_id = team_obj.search(cr, uid, [('code','ilike','BERSAV')])

        atom_team_id = team_obj.browse(cr, uid, a_team_id)
        beraud_team_id = team_obj.browse(cr, uid, b_team_id)

        for repair in self.browse(cr, uid, ids, context=context):
            i_id = res[repair.id]
            inv_id = inv_obj.browse(cr, uid, i_id)

            if inv_id:
                if repair.company_id.id == 1:
                    inv_id.sudo().team_id = beraud_team_id
                else:
                    inv_id.sudo().team_id = atom_team_id.id

                #### get the right account for each line #####

                for line in inv_id.invoice_line_ids:
                    account_env = self.pool.get('account.account')
                    partner_company_id = repair.partner_id.company_id.id

                    account_code = account_env.search_read(cr, 1, [('id', '=', line.account_id.id)])
                    account_id = account_env.search(cr, 1, [('code', '=', account_code[0]['code']), ('company_id', '=', partner_company_id)])
                    print 'account_id    :   ', account_id
                    if account_id:
                        account_id = account_id[0]
                    fpos = repair.partner_id.property_account_position_id
                    if fpos:
                        account_id = fpos.map_account(account_env.browse(cr, uid, account_id, context))
                    line.account_id = account_id

        return res

    def get_loc_from_tech(self, tech):
        loc_obj = self.env['stock.location']
        t_loc_id = loc_obj.search([('tech', 'ilike', tech.name)])
        return t_loc_id

    def get_tech_loc(self):
        loc_obj = self.env['stock.location']
        t_loc_id = loc_obj.search([('tech', 'ilike', self.tech.name)])
        return t_loc_id


class MrpRepairLine(models.Model):

    _inherit = 'mrp.repair.line'

    # if a line is created or removed while a repair is ongoing
    # state either 'confirmed' or 'started', create move, reserve it,
    # and store it here.
    associated_move = fields.Many2one('stock.move')
    to_invoice = fields.Boolean(default=True)
    #tech_name = fields.Many2one(related='repair_id.tech', store=True)

    # called by the repair_id onchange on the tech. So the tech has changed
    def update_line(self):
        ''' set depending on line type, '''
        print "[%s] mrp_repair_line UPDATE_LINE" % __name__

        loc_obj = self.env['stock.location']
        ber_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        atom_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        customer_loc_id = loc_obj.search([('complete_name','ilike','Partner Locations/Customers')])

        error = 0
        for line in self:
            stock_loc_id = ber_loc_id if line.repair_id.company_id.id == 1 else atom_loc_id
            if line.type == 'add':
                #import pudb;pudb.set_trace();
                line.location_id = line.repair_id.get_loc_from_tech(line.repair_id.tech).id or stock_loc_id
                line.location_dest_id = line.repair_id.location_dest_id.id # customer loc id
            else:
                line.location_id = line.repair_id.location_dest_id.id #customer loc
                line.location_dest_id = line.repair_id.get_loc_from_tech(line.repair_id.tech).id or stock_loc_id
            if not line.repair_id.get_loc_from_tech(line.repair_id.tech):
                error += 1
        return error

    @api.model
    def create(self, vals):
        print "[%s] mrp_repair_line CREATE" % __name__
        ''' set the locations of the lines at creation time if we are in the correct states '''

        loc_obj = self.env['stock.location']
        ber_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        atom_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])

        if not vals.get('location_id'):
            vals.update({'location_id': ber_loc_id.id})
        if not vals.get('location_dest_id'):
            vals.update({'location_dest_id': ber_loc_id.id})

        repair_line = super(MrpRepairLine, self).create(vals)

        tech = repair_line.repair_id.tech

        print 'tech name is : ', repair_line.repair_id.tech.name
        # if there's a tech and we are in these states, set the right locations and return
        # without making move (move will be made when repair is ended)
        if tech :
            tech_loc_id = loc_obj.search([('tech', 'ilike', tech.name)])
            # check for errors getting the tech loc id
            if not tech_loc_id:
                raise UserError("Problem while finding the tech location. He probably has no location assigned.")
            # line from tech stock to client stock 
            repair_line.location_id = tech_loc_id.id
            repair_line.location_dest_id = repair_line.repair_id.location_dest_id.id
            return repair_line

        # if there's no tech and we are not in these states, do nothing more, just create the line
        if repair_line.repair_id.state not in ('confirmed', 'ready', 'under_repair'):
            return repair_line

        # if there is no tech and we are in the right states, create move associated with the line
        move_obj = self.env['stock.move']
        repair_obj = self.env['mrp.repair']
        customer_loc_id = loc_obj.search([('complete_name','ilike','Partner Locations/Customers')])
        prod_loc_id = loc_obj.search([('complete_name','ilike','Virtual Locations/Production')])

        p_comp_id = repair_line.repair_id.partner_id.company_id.id
        line_type = repair_line.type

        stock_loc_id = ber_loc_id
        print 'p_comp_id : ', p_comp_id
        if p_comp_id == 3:
            stock_loc_id = atom_loc_id

        orig_loc_id = stock_loc_id
        dest_loc_id = prod_loc_id
        print 'line_type : ', line_type
        if line_type == 'remove' :
            orig_loc_id = customer_loc_id
            dest_loc_id = stock_loc_id

        if (not orig_loc_id) or (not dest_loc_id):
            raise UserError("Il y a eu un problème lors de la sélection des emplacements source/destination de la ligne.")

        # update repair_line with the right info so it creates OK
        # these assigns generate writes (write is called)
        repair_line.location_id = orig_loc_id
        repair_line.location_dest_id = dest_loc_id

        # if there's no tech and we are in the right states, create the move
        print "REPAIR_LINE IS : ", repair_line
        print "state of repair of repair_line is : ", repair_line.repair_id.state
        print "orig_loc_id is : ", orig_loc_id
        print "dest_loc_id is : ", dest_loc_id

        # now we can create the move
        move_id = move_obj.create({
            'origin': repair_line.repair_id.name,
            'name': repair_line.name,
            'product_uom': repair_line.product_id.uom_id.id,
            'product_id': repair_line.product_id.id,
            'product_uom_qty': repair_line.product_uom_qty,

            'location_id': orig_loc_id.id, # line location
            'location_dest_id': dest_loc_id.id, #line location

            'restrict_lot_id': repair_line.lot_id.id,
        })

        # confirm it and assign it (reservation)
        move_id.action_confirm()
        move_id.action_assign()
        print "created move corresponding to newly created line : ", move_id

        # update the move in mrp.repair.line, and moves in repair.linked_moves
        repair_line.associated_move = move_id
        repair_line.repair_id.write({'linked_moves' : [(4, move_id.id)] })
        print "repair.linked_moves are now : ", repair_line.repair_id.linked_moves

        return repair_line


    @api.multi
    def write(self, vals):
        print "[%s] mrp_repair_line WRITE" % __name__

        loc_obj = self.env['stock.location']
        ber_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        atom_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        customer_loc_id = loc_obj.search([('complete_name','ilike','Partner Locations/Customers')])
        prod_loc_id = loc_obj.search([('complete_name','ilike','Virtual Locations/Production')])

        for repair_line in self:

            # if we are in the states when we do weird things at create time on the lines, don't do
            # anything more in the write
            if repair_line.repair_id.tech :#and repair_line.repair_id.state in ('confirmed', 'ready', 'under_repair'):
                print '[write] there is a tech, doing the tech line stuff'
                vals.update(repair_line.get_tech_line_vals(repair_line))
                super(MrpRepairLine, repair_line).write(vals)
                continue

            # no tech and states when we do moves
            if repair_line.repair_id.state in ('confirmed', 'ready', 'under_repair'):
                print "[write] there is _no_ tech, we're in the states to do the moves, doing the move line stuff"
                vals.update(repair_line.get_move_line_vals(repair_line))
                super(MrpRepairLine, repair_line).write(vals)
                repair_line.modify_move_line(repair_line)
                continue

            # no tech, and we are not in the states where we do the moves
            print "[write] there is _no_ tech, we're _not_ in the states to do the moves, doing the move line stuff, not modifying moves"
            vals.update(repair_line.get_move_line_vals(repair_line))
            super(MrpRepairLine, repair_line).write(vals)


    def get_tech_line_vals(self, line):
        print "[%s] mrp_repair_line GET_TECH_LINE_VALS" % __name__

        loc_obj = self.env['stock.location']
        ber_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        atom_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        customer_loc_id = loc_obj.search([('complete_name','ilike','Partner Locations/Customers')])
        prod_loc_id = loc_obj.search([('complete_name','ilike','Virtual Locations/Production')])
        stock_loc_id = ber_loc_id if line.repair_id.company_id.id == 1 else atom_loc_id

        vals = {}
        if line.type == 'add':
            vals.update({'location_id': stock_loc_id.id,
                    'location_dest_id': line.repair_id.get_tech_loc().id})
        else :
            vals.update({'location_id': customer_loc_id.id,
                    'location_dest_id': line.repair_id.get_tech_loc().id})
        return vals

    def get_move_line_vals(self, line):
        print "[%s] mrp_repair_line GET_MOVE_LINE_VALS" % __name__

        loc_obj = self.env['stock.location']
        ber_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DC/Stock')])
        atom_loc_id = loc_obj.search([('complete_name','ilike','Physical Locations/DAT/Stock')])
        customer_loc_id = loc_obj.search([('complete_name','ilike','Partner Locations/Customers')])
        prod_loc_id = loc_obj.search([('complete_name','ilike','Virtual Locations/Production')])
        stock_loc_id = ber_loc_id if line.repair_id.company_id.id == 1 else atom_loc_id

        vals = {}
        if line.type == 'add':
            vals.update({'location_id': stock_loc_id.id,
                    'location_dest_id': prod_loc_id.id})
        else :
            vals.update({'location_id': customer_loc_id.id,
                    'location_dest_id': stock_loc_id.id})
        return vals

    def modify_move_line(self, line):
        print "[%s] mrp_repair_line WRITE_LINE_WITH_MOVE" % __name__
        # if there is an associated move, unreserve it, modify it, reserve it again

        if line.associated_move : 
            line.associated_move.do_unreserve()

            line.associated_move.write({
                'product_uom': line.product_id.uom_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,

                #'location_id': repair_line.location_id.id, # line location
                #'location_dest_id': repair_line.location_dest_id.id, #line location
                #'location_id': orig_loc_id.id, # line location
                #'location_dest_id': dest_loc_id.id, #line location

                'location_id': line.location_id.id, # line location
                'location_dest_id': line.location_dest_id.id, #line location

                'restrict_lot_id': line.lot_id.id,
            })
            line.associated_move.action_assign()

    @api.multi
    def unlink(self):
        print "*** MRP_REPAIR_LINE our unlink"
        for repair_line in self:
            if repair_line.associated_move :
                # first we remove the move from repair_id.linked_moves
                for move in repair_line.repair_id.linked_moves:
                    if move.id == repair_line.associated_move.id : 
                        print "repair_id.linked_moves before ", repair_line.repair_id.linked_moves
                        repair_line.repair_id.write({'linked_moves' : [(3, move.id)] })
                        print "repair_id.linked_moves after ", repair_line.repair_id.linked_moves

                        # then we cancel the move
                        print "going to cancel move : ", repair_line.associated_move
                        repair_line.associated_move.action_cancel()
                        print "cancelled move  : ", repair_line.associated_move.state

        return super(MrpRepairLine, self).unlink()

    def onchange_operation_type(self, cr, uid, ids, type, guarantee_limit, company_id=False, context=None):
        res = super(MrpRepairLine, self).onchange_operation_type(cr, uid, ids, type, guarantee_limit, company_id=company_id, context=context)
        res['value']['to_invoice'] = True

        return res


class StockQuant(models.Model):

    _inherit = 'stock.quant'

    # holds the stock location the quant came form initially
    # useful only in the context of repairs, so we can trace where the piece came from,
    # and check it against the company_id of the Customer it was used for.
    #origin = fields.Many2one('stock.location')
    #origin = fields.Char(string="Source Document")
    origin = fields.Many2one('res.company')

class StockMove(models.Model):

    _inherit = 'stock.move'

    # override action_done, and add origin to quants
    def action_done(self, cr, uid, ids, context=None):
        # call super
        # get all quants with our move_id, and set their origin to
        # the company_id of the stock_location they come from.
        # It will be the company stock their belonged to "originally", 
        # before they were used for a repair.

        print "STOCK_MOVE our action_done"
        print 'stock_move_ids : ', ids

        super(StockMove, self).action_done(cr, uid, ids, context)

        for move in self.browse(cr, uid, ids, context=context):

            for quant in move.quant_ids : 
                quant.sudo().origin = quant.sudo().company_id
                print "*** quant origin in move id _%s_ set to _%s_ ***" % (move.id, move.origin)

