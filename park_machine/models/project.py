# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.osv import expression


# class ProjectProject(models.Model):
#     _inherit = 'project.project'


class Task(models.Model):
    _inherit = 'project.task'

    sale_ids = fields.One2many(string="sales", comodel_name='sale.order', compute="_compute_sale_ids")

    def _compute_sale_ids(self):
        for task in self:
            sales = self.env['sale.order'].search([('task_id', '=', task.id)])
            task.sale_ids = [(6, False, sales.ids)]
