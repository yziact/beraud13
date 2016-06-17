# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class ProductTemplate(models.Model):
    _inherit = "product.template"

    code_douane = fields.Char('Code douane')

