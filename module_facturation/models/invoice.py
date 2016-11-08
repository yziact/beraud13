from openerp import models, api, fields


class AccountInvoiceInherit(models.Model):
    _inherit = 'account.invoice'

    partner_shipping_id = fields.Many2one('res.partner', string='Adresse de Livraison', readonly=True, required=True,
                                          states={'draft': [('readonly', False)]}, help="Delivery address for current sales order.")

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Delivery address
        """
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
