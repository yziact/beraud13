# coding = utf-8

from openerp import models, api
import logging 

_logger = logging.getLogger(__name__)

class MrpRepair(models.Model):
    _inherit = 'mrp.repair'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(MrpRepair, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        _logger.error("Inside of fields_view_get MrpRepair")
        #if self._context.get('purchase_order', False):
        #_logger.error("self._context.get of mrp_repair : %s", self._context.get('mrp_repair'))
        #if self._context.get('mrp_repair', False):
        report_quotation = self.env.ref(
                'mrp_repair.action_report_mrp_repair_order')
        _logger.error("report_quotation : %s", report_quotation)
        _logger.error("report_quotation xml_id : %s", report_quotation.xml_id)
        _logger.error("report_quotation id : %s", report_quotation.id)

        #view_id = self.env['ir.model.data'].xmlid_to_res_id('mrp_repair.report_mrprepairorder')
        #view_id = self.env['ir.model.data'].xmlid_to_res_id('mrp_repair.action_report_mrp_repair_order')
        #_logger.error("VIEW ID 1 : %s", view_id)

        #_logger.error("res toolbar print : %s", res['toolbar']['print'])
        for print_submenu in res.get('toolbar', {}).get('print', []):
            _logger.error("print submenu : %s", print_submenu)
            if print_submenu['id'] == report_quotation.id:
                res['toolbar']['print'].remove(print_submenu)

        return res

