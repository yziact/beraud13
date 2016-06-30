# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class ProductTemplate(models.Model):
    _inherit = "product.template"

    code_douane = fields.Char('Code douane')

class ProductCategory(models.Model):
    _inherit = "product.category"

    is_machine = fields.Boolean(string=u"Catégorie de machine")


