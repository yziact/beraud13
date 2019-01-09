from openerp import models, api, fields
from openerp.tools import float_compare


class AccountInvoiceInherit(models.Model):
    _inherit = 'account.invoice'

    def _default_commercial(self):
        if not self.contact_affaire:
            return self.env.user

    contact_affaire = fields.Many2one('res.users', string='V/Contact affaire', default=_default_commercial)
    partner_shipping_id = fields.Many2one('res.partner', string='Adresse de Livraison', readonly=True, states={'draft': [('readonly', False)]}, help="Delivery address for current sales order.")

    last_bl_from_bc = fields.Many2one('stock.picking', string='Last Validated BL linked to BC', readonly=True,
                                     store=True)
    bl_date = fields.Date('Date Bon livraison')

    contact = fields.Many2one('res.partner', readonly=True,
                              states={'draft': [('readonly', False)], 'proforma2': [('readonly', False)]})

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id')
    def _compute_amount(self):
        self.amount_untaxed = "{0:.2f}".format(sum(line.price_subtotal for line in self.invoice_line_ids))
        self.amount_tax = "{0:.2f}".format(sum(line.amount for line in self.tax_line_ids))
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            amount_total_company_signed = self.currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = self.currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign



    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Delivery address
        """
        super(AccountInvoiceInherit, self)._onchange_partner_id()

        if self.type in ['out_invoice', 'out_refund']:
            if not self.partner_id:
                self.update({
                    'partner_shipping_id': False,
                })
                return

            addr = self.partner_id.address_get(['delivery'])

            values = {
                'partner_shipping_id': addr['delivery'],
            }
            self.update(values)


    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):

        res = super(AccountInvoiceInherit, self).refund(date_invoice, date, description, journal_id)

        if self.type in ['out_invoice', 'out_refund']:
            if not self.partner_id:
                res['partner_shipping_id'] = False
            else :
                addr = res['partner_id'].address_get(['delivery'])
                res['partner_shipping_id'] =  addr['delivery']

        return res


    @api.multi
    def fix_me(self):
        # invoice_ids = self.search([('id', '=', 302)])
        move_env = self.env['account.move']
        move_line_env = self.env['account.move.line']
        for invoice in self:
            move_obj = move_env.search([('id', '=', invoice.move_id.id)])
            move_line = move_line_env.search([('move_id', '=', move_obj.id)])

            if not invoice.state in ['draft']:
                for line in move_line:
                    move_line_env._cr.execute("DELETE FROM account_move_line WHERE move_id=%s ", (move_obj.id,))

                invoice.move_id = None
                move_env._cr.execute("DELETE FROM account_move WHERE id=%s", (move_obj.id,))

            if invoice.invoice_line_ids:

                sale_line = invoice.invoice_line_ids[0].sale_line_ids
                sale = sale_line.order_id

                if sale and sale.last_picking_id:
                    # print sale.last_picking_id.id

                    invoice.write({'last_bl_from_bc': sale.last_picking_id.id,
                                   'bl_date': sale.last_picking_id_date_done})

                # if invoice.create_date > '2016-12-01':
                TTHT = 0
                TVA = 0
                for line in invoice.invoice_line_ids:
                    sub_tt = line.quantity * (line.price_unit * (1 - (line.discount / 100.0)))
                    TTHT += sub_tt
                    line.price_subtotal = sub_tt
                    TVA += 20 * sub_tt / 100

                for tax in invoice.tax_line_ids:
                    tax.amount = "{0:.2f}".format(TVA)

                invoice._compute_amount()
                invoice.action_move_create()


class inherit_AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    num_bl = fields.Char('Num BL/OR')
    serial = fields.Char('Num serie')
