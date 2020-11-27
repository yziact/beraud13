# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    location_id = fields.Many2one(string="Location", comodel_name='stock.location', compute="_compute_location_id")
    partner_id = fields.Many2one(string="Customer", comodel_name='res.partner')
    customer_location = fields.Many2one(string="Customer location", comodel_name='res.partner',
                                        compute="_compute_customer_location")

    task_ids = fields.One2many(string="Interventions", comodel_name='project.task', compute="_compute_task_ids")

    # Try to not store count, but they're used… What could go wrong ?
    tasks_count = fields.Integer(string="Tasks count", store=False, compute="_compute_task_ids")
    implementation_date = fields.Date(string="implementation date", compute="_compute_implementation_date")
    warranty_date_end = fields.Date(string="Warrany date end")
    note = fields.Html(string='Comments')
    is_maintenance_contract = fields.Boolean(string="Maintenance contract")

    @api.depends('partner_id')
    def _compute_customer_location(self):
        for partner in self:
            partner.customer_location = False
            # The delivery picking of the last order (2 l.)
            order_ids = partner.sale_order_ids
            if order_ids:
                order_id = order_ids[0]
                delivery_picking = order_id.picking_ids.filtered(lambda x: x.picking_type_id.code == "outgoing")
                if delivery_picking and delivery_picking.partner_id:
                    partner.customer_location = delivery_picking.partner_id.id


    def _compute_location_id(self):
        """
        The location is the destination of the last BL in state DONE,
        Do not confuse with the client location. (Can be the client location, of course).
        """
        for lot in self:
            sml = self.env['stock.move.line'].search([
                ('lot_id', '=', lot.id),
                ('state', '=', "done"),
                ], order="date desc", limit=1
            )
            lot.location_id = sml.location_dest_id.id

    def _compute_task_ids(self):
        for lot in self:
            task_ids = self.env['project.task'].search([('lot_id', '=', lot.id), ('is_fsm', '=', True)])
            lot.tasks_count = len(task_ids)
            lot.task_ids = [(6, False, task_ids.ids)]

    def _compute_implementation_date(self):
        """
        The implementation date is corresponding to the first delivery in client location.
        """
        for lot in self:
            sml = self.env['stock.move.line'].search([
                ('lot_id', '=', lot.id),
                ('picking_id.picking_type_id.code', '=', "outgoing")],
                order="date asc", limit=1
            )
            lot.implementation_date = sml.picking_id.date_done
