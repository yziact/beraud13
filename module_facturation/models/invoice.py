from openerp import models, api, fields


class AccountInvoiceInherit(models.Model):
    _inherit = 'account.invoice'

    partner_shipping_id = fields.Many2one('res.partner', string='Adresse de Livraison', readonly=True, states={'draft': [('readonly', False)]}, help="Delivery address for current sales order.")

    @api.multi
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
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


