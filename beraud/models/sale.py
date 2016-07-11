# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    name = fields.Html(string='Description', required=True)



class SaleAdvancePaymentInvoice(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    advance_payment_method = fields.Selection(selection_add=[('proforma', 'Proforma')])

    @api.multi
    def create_invoices(self):
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


