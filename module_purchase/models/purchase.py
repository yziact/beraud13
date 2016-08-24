# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
import logging 

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """ enlever le menu des rapport par défaut.  """

        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        #_logger.error('Purchase Order Fields View Get')
        if not res.get('toolbar', {}).get('print', []):
            #_logger.error('print menu empty, returning unaltered view.')
            return res

        # this is for removal of the reports instead of the actions. Also removes the whole print menu it seems.
        # we'll do it this way here. In module_reparations we do it the other way round, removing the actions.
        report_id_list = []
        report_id_list.append(self.env['report']._get_report_from_name('purchase.report_purchaseorder').id)
        report_id_list.append(self.env['report']._get_report_from_name('purchase.report_purchasequotation').id)

        res['toolbar']['print'] = [dict(t) for t in res.get('toolbar', {}).get('print', []) if t['id'] not in report_id_list]

        return res 


