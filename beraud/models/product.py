# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class ProductTemplate(models.Model):
    _inherit = "product.template"

    code_douane = fields.Char('Code douane')

    description_purchase= fields.Html('Purchase Description', translate=True)
    description_sale = fields.Html('Sale Description', translate=True)
    description_picking = fields.Html('Picking Description', translate=True)

    nb_palette = fields.Integer('Nombre de palettes')

    allee = fields.Char('Allée')
    casier = fields.Char('Casier')


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_machine = fields.Boolean(string=u"Catégorie de machine")


