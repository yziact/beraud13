# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_machine_category = fields.Boolean('Is machine category', default=False)
