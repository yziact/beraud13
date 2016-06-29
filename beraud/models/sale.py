# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    name = fields.Html(string='Description', required=True)