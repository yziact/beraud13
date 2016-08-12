# -*- coding: utf-8 -*-

# old api imports
import openerp
from openerp.osv import fields, osv
from openerp.tools.float_utils import float_compare, float_round
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api, models
import openerp.addons.decimal_precision as dp
from openerp.addons.procurement import procurement
import logging
from openerp.exceptions import UserError

# new api imports
from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class stock_warehouse(models.Model): 
    _inherit = "stock.warehouse" 

    # use decorator to be able to use old api...
    @api.V7
    def create_sequences_and_picking_types(self, cr, uid, warehouse, context=None):
        pass


