
from openerp import models, api, fields


class StockPickinInherit(models.Model):
    _inherit = "stock.picking"

    incoterm_id = fields.Many2one('stock.incoterms', 'Incoterms')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """ enlever le menu du rapport par défaut.  """

        res = super(StockPickinInherit, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        print 'MU'

        if not res.get('toolbar', {}).get('print', []):
            print 'BLABLA'
            return res

        report_quotation = self.env.ref('stock.action_report_picking')
        res['toolbar']['print'] = [dict(t) for t in res.get('toolbar', {}).get('print', []) if
                                   t['id'] != report_quotation.id]
        return res
