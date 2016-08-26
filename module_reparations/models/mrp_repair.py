# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
import logging 

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
from utilsmod import utilsmod

_logger = logging.getLogger(__name__)

class MrpRepair(models.Model):
    _inherit = 'mrp.repair'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        mask = utilsmod.ReportMask(['mrp_repair.action_report_mrp_repair_order'])
        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(res, self)

    # not visible to the model until created, but exists in db
    create_date = fields.Datetime('Create Date', readonly=True)

    date_start = fields.Datetime(string='Date de début', required=True, store=True, index=True, copy=False, default=fields.Datetime.now, help="Date du début de la réparation")

    end_date = fields.Datetime(string="Date de fin", required=True, store=True, help="Date prévue de la fin de la réparation")

    invoice_method = fields.Selection(default='after_repair')


