from openerp import models, api, fields


class SaleInherit(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        print "[%s] our _prepare_invoice" % __name__

        res = super(SaleInherit, self)._prepare_invoice()

        res['partner_shipping_id'] = self.partner_shipping_id.id
        res['date_invoice'] = self.last_picking_id_date_done
        res['last_bl_from_bc'] = self.last_picking_id.id

        if self.contact:
            res['contact'] = self.contact.id
        print res

        return res

