
# -*- coding: utf-8 -*-

from openerp import models, api, fields
from lxml import etree
import datetime

import logging
_logger = logging.getLogger(__name__)

import pprint
pp = pprint.PrettyPrinter(indent=2)

import datetime

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    # make create_date editable
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True, 
                                 states={
                                     'draft': [('readonly', False)],
                                     'sent': [('readonly', False)],
                                     'sale': [('readonly', False)],
                                 },
                                 copy=False, default=fields.Datetime.now)

