from openerp import models, api, fields


class SaleInherit(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):

        res = super(SaleInherit, self)._prepare_invoice()

        res['partner_shipping_id'] = self.partner_shipping_id.id

        print res

        return res
