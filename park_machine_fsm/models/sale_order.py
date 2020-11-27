# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _timesheet_create_task(self, project):
        res = super(SaleOrder, self)._timesheet_create_task(project)
        res.ticket_id = self.ticket_id

