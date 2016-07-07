# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class ProductTemplate(models.Model):
    _inherit = "product.template"

    code_douane = fields.Char('Code douane')

    description_purchase= fields.Html('Purchase Description',translate=True)
    description_sale = fields.Html('Sale Description',translate=True)
    description_picking = fields.Html('Picking Description', translate=True)


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_machine = fields.Boolean(string=u"Catégorie de machine")


