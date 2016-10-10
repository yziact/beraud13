# -*- coding: utf-8 -*-
##############################################################################
#
#    herbarom module for OpenERP, Module Herbarom
#    Copyright (C) 2015 Smile
#              Chris Tribbeck <chris.tribbeck@smile.eu>
#
#    This file is a part of herbarom
#
#    herbarom is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    herbarom is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields
from openerp.tools.translate import _
from openerp.exceptions import UserError


class wizard_transfer_stock_intercompany_line(models.TransientModel):
    _name = "wizard.transfer.stock.intercompany.line"
    _description = "Intercompany transfer stock lines"

    wizard_id = fields.Many2one('wizard.transfer.stock.intercompany', string='Wizard')
    restrict_lot_id = fields.Many2one('stock.production.lot', string='Lot', help='Select the lot id if required.')
    quantity = fields.Float(string='Quantity', digits=(16, 8), help="Enter the quantity to transfer.")
    product_id = fields.Many2one('product.product', string='Product', help='Select the product.', required=True, )
    stock_move_id = fields.Many2one('stock.move', string='Movement', help='Any linked stock move.')


class wizard_transfer_stock_intercompany(models.TransientModel):
    _name = "wizard.transfer.stock.intercompany"
    _description = "Intercompany stock transfer wizard"

    line_ids = fields.One2many('wizard.transfer.stock.intercompany.line', 'wizard_id', string='Lines', help='Create or edit the lines.')
    company_src_id = fields.Many2one('res.company', string='Source company', help='Select the source company.', required=True, )
    location_src_id = fields.Many2one('stock.location', string='Source location', help='Select the source location.', required=True, )
    company_dst_id = fields.Many2one('res.company', string='Destination company', help='Select the destination company.', required=True, )
    location_dst_id = fields.Many2one('stock.location', string='Destination location', help='Select the destination location.', required=True, )
    production_id = fields.Many2one('mrp.production', string='Production', help='The production.')
    picking_id = fields.Many2one('stock.picking', string='Picking', help='The stock picking.')
    update_data = fields.Boolean(string='Update', help='Check this box if the product list is to be updated on changing the company source and/or destination', default=True)
    is_ok = fields.Boolean(string='Is ok', compute='_get_is_ok', )

    @api.multi
    def _get_is_ok(self):
        for wizard in self:
            wizard.is_ok = len(wizard.line_ids) > 0 and (wizard.company_src_id != wizard.company_dst_id) and wizard.company_src_id and wizard.company_dst_id

    @api.model
    def default_get(self, fields_list):
        """
        Get the appropriate lines (if any)
        """
        values = super(wizard_transfer_stock_intercompany, self).default_get(fields_list)
        # values['company_dst_id'] = self.env.user.company_id.id
        if self.env.context.get('active_id'):
            model = self.env.context.get('active_model')
            lines = []
            if model == 'mrp.production':
                # Get all lines that have not yet been reserved
                production = self.env['mrp.production'].browse(self.env.context['active_id'])
                values['production_id'] = production.id
                values['company_dst_id'] = production.company_id.id
                values['location_dst_id'] = production.location_src_id.id
                values['location_src_id'] = production.location_src_id.id
                cur_company = False
                for line in production.move_lines:
                    if line.product_id.company_id != production.company_id and line.state in ('draft', 'confirmed'):
                        if not cur_company or cur_company == line.product_id.company_id:
                            lines.append(
                                (0, 0, {
                                    'product_id': line.product_id.id,
                                    'quantity': line.product_uom_qty,
                                    'restrict_lot_id': line.restrict_lot_id.id,
                                    'stock_move_id': line.id,
                                })
                            )
                            cur_company = line.product_id.company_id
                if cur_company:
                    values['company_src_id'] = cur_company.id

            elif model == "stock.picking":
                # Get all lines that have not yet been reserved
                picking = self.env['stock.picking'].browse(self.env.context['active_id'])
                values['picking_id'] = picking.id
                values['company_dst_id'] = picking.company_id.id
                values['location_dst_id'] = picking.location_id.id
                values['location_src_id'] = picking.location_id.id
                cur_company = False
                for line in picking.move_lines:
                    if line.product_id.company_id != picking.company_id and line.state in ('draft', 'confirmed'):
                        if not cur_company or cur_company == line.product_id.company_id:
                            lines.append(
                                (0, 0, {
                                    'product_id': line.product_id.id,
                                    'quantity': line.product_uom_qty,
                                    'restrict_lot_id': line.restrict_lot_id.id,
                                    'stock_move_id': line.id,
                                })
                            )
                            cur_company = line.product_id.company_id
                if cur_company:
                    values['company_src_id'] = cur_company.id

            elif model == "stock.quant":
                # Create a line for the quant in question
                quant = self.env['stock.quant'].browse(self.env.context['active_id'])
                values['company_src_id'] = quant.company_id.id
                values['location_src_id'] = quant.location_id.id
                lines.append(
                    (0, 0, {
                        'product_id': quant.product_id.id,
                        'quantity': quant.qty,
                        'restrict_lot_id': quant.lot_id.id,
                    })
                )

            values['line_ids'] = lines

        """
        else:
            warehouses = self.env['stock.warehouse'].search([
                ('company_id', '=', self.env.user.company_id.id),
            ], limit=1)
            if not warehouses:
                warehouses = self.env['stock.warehouse'].search([
                    ('company_id', 'parent_of', self.env.user.company_id.id),
                ], limit=1)
            if warehouses:
                values['location_dst_id'] = warehouses.lot_stock_id.id
        """

        return values

    @api.multi
    def perform_transfer(self):
        """
        Perform the transfer by :
            1) Creating 2 stock moves:
                - source to the transit location on company source
                - transit location to destination location on company destination
            2) Confirm, reserve and execute the first move
            3) Confirm and force the second move
            4) If there is a linked move (for example, productions), perform the reservation of the linked move - this is done with the linked move (move_dest_id)
        """
        move_obj = self.env['stock.move']
        company_env = self.env['res.company']
        moves = [] 

        for wizard in self:
            location_trn = self.env['stock.location'].search([
                ('usage', '=', 'transit'),
                ('company_id', '=', wizard.company_dst_id.id),
            ], limit=1)
            if not location_trn:
                # Use a generic one
                location_trn = self.env['stock.location'].search([
                    ('usage', '=', 'transit'),
                    ('company_id', '=', False),
                ], limit=1)
            if not location_trn:
                raise UserError(_("No stock transit location could be found!"))

            for line in wizard.line_ids:
                move_vals = {
                    'name': _('Intercompany transit %s - Source') % (line.product_id.name),
                    'origin': 'TSIS move',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'company_id': wizard.company_src_id.id,
                    'location_id': wizard.location_src_id.id,
                    'location_dest_id': location_trn.id,
                    'restrict_lot_id': line.restrict_lot_id.id,
                    'partner_id': wizard.company_dst_id.partner_id.id,
                    'isSale': True
                }
                move1 = move_obj.create(move_vals)

                move_vals.update({
                    'name': _('Intercompany transit %s - Destination') % (line.product_id.name),
                    'company_id': wizard.company_dst_id.id,
                    'location_id': location_trn.id,
                    'location_dest_id': wizard.location_dst_id.id,
                    'move_dest_id': line.stock_move_id.id,
                    'partner_id': wizard.company_src_id.partner_id.id,
                    'isSale': False
                })
                move2 = move_obj.create(move_vals)

                move1.action_confirm()
                if move1.state != 'confirmed':
                    raise UserError(_("The first movement could not be confirmed!"))

                move1.action_done()
                if move1.state != 'done':
                    raise UserError(_("The first movement could not be terminated!"))

                print "MOVE 1 QUANT IDS : ",move1.sudo().quant_ids
                # set owner of quant to company that received the move
                move1.sudo().quant_ids.write({'company_id': wizard.company_dst_id.id})

                move2.action_confirm()
                if move2.state != 'confirmed':
                    raise UserError(_("The second movement could not be confirmed!"))

                move2.action_done()
                if move2.state != 'done':
                    raise UserError(_("The second movement could not be terminated!"))

                print "MOVE 2 QUANT IDS : ",move2.sudo().quant_ids
                moves.append((move1, move2))

        # returning moves to easily fetch them from tests
        return moves


    @api.onchange('company_src_id', 'company_dst_id')
    def onchange_company_src_dst_id(self):
        if self.update_data and (self.production_id or self.picking_id):
            lines = [(5, 0, 0)]
            if self.production_id:
                for line in self.production_id.move_lines:
                    if line.product_id.company_id != self.company_dst_id and line.state in ('draft', 'confirmed'):
                        if line.product_id.company_id == self.company_src_id:
                            lines.append(
                                (0, 0, {
                                    'product_id': line.product_id.id,
                                    'quantity': line.product_uom_qty,
                                    'restrict_lot_id': line.restrict_lot_id.id,
                                    'stock_move_id': line.id,
                                })
                            )

            elif self.picking_id:
                for line in self.picking_id.move_lines:
                    if line.product_id.company_id != self.company_dst_id and line.state in ('draft', 'confirmed'):
                        if line.product_id.company_id == self.company_src_id:
                            lines.append(
                                (0, 0, {
                                    'product_id': line.product_id.id,
                                    'quantity': line.product_uom_qty,
                                    'restrict_lot_id': line.restrict_lot_id.id,
                                    'stock_move_id': line.id,
                                })
                            )

            self.line_ids = lines
        self.is_ok = len(self.line_ids) > 0 and (self.company_src_id != self.company_dst_id) and self.company_src_id and self.company_dst_id

    @api.onchange('company_src_id')
    def onchange_company_src_id(self):
        if not self.location_src_id:
            warehouses = self.env['stock.warehouse'].search([
                ('company_id', '=', self.company_src_id.id),
            ], limit=1)
            if not warehouses:
                warehouses = self.env['stock.warehouse'].search([
                    ('company_id', 'parent_of', self.company_src_id.id),
                ], limit=1)
            if warehouses:
                self.location_src_id = warehouses.lot_stock_id.id

    @api.onchange('line_ids')
    def onchange_line_ids(self):
        print self.line_ids, len(self.line_ids)
        self.is_ok = len(self.line_ids) > 0 and (self.company_src_id != self.company_dst_id) and self.company_src_id and self.company_dst_id


