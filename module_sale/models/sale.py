# -*- coding: utf-8 -*-

from openerp import models, api, fields
from lxml import etree
import datetime

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')
from utilsmod import utilsmod

import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    name = fields.Html(string='Description', required=True, default_focus=True)


class SaleAdvancePaymentInvoice(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    advance_payment_method = fields.Selection(selection_add=[('proforma', 'Proforma')])

    @api.multi
    def create_invoices(self):
        #print "*** our create invoices"
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        ret = {}

        if self.advance_payment_method == 'proforma':
            for order in sale_orders:
                for line in order.order_line:
                    line.qty_to_invoice = line.product_uom_qty

            inv_ids = sale_orders.action_invoice_create(final=True)
            for invoice in self.env['account.invoice'].browse( inv_ids ):
                invoice.state = 'proforma2'

            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()

            return {'type': 'ir.actions.act_window_close'}

        else:
            ret = super(SaleAdvancePaymentInvoice, self).create_invoices()
            return ret

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    contact = fields.Many2one('res.partner', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    commercial = fields.Many2one('res.users', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        mask = utilsmod.ReportMask(['module_sale.report_mysaleorder'])
        res = super(SaleOrderInherit, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(res, self)


