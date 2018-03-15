# -*- coding: utf-8 -*-



from openerp import models, api, fields, _
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class Figures:
    _inherit = 'crm.stage'
    _inherit = 'sale.order'

    # date_order = fields.

