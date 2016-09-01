# -*- coding: utf-8 -*-

from openerp import models, api, fields

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
from utilsmod import utilsmod

import logging 
_logger = logging.getLogger(__name__)

class StockPickingInherit(models.Model):
    _inherit = "stock.picking"

    incoterm_id = fields.Many2one('stock.incoterms', 'Incoterms')

    #report_quotation = self.env.ref('module_stocks._report_picking')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        #mask = utilsmod.ReportMask(['module_stocks.report_my_picking', 'module_stocks.report_my_shipping2'])
        mask = utilsmod.ReportMask(['module_stocks.report_my_picking'])
        res = super(StockPickingInherit, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(res, self)


    def action_assign(self, cr, uid, ids, context=None):
        pass

