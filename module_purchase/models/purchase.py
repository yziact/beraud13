# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
sys.path.insert(0, '/mnt/extra-addons/')
from utilsmod import utilsmod

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _default_commercial(self):
        print "OUR DEFAULT COMMERCIAL"
        print self.env.context
        print self.env.user

        if not self.contact_affaire:
            return self.env.user

    contact_affaire = fields.Many2one('res.users', string='V/Contact affaire', default=_default_commercial)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)


    contact = fields.Many2one('res.partner', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(PurchaseOrder, self).onchange_partner_id()
        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        mask = utilsmod.ReportMask(['module_purchase.report_mypurchaseorder'])
        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(res, self)

    READONLY_STATES = {
        'purchase': [('readonly', False)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    date_order = fields.Datetime('Order Date', required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Datetime.now,\
        help="Depicts the date where the Quotation should be validated and converted into a purchase order.")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    name = fields.Html()
