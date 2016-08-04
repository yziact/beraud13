# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging 

_logger = logging.getLogger(__name__)

class MrpRepair(models.Model):
    _inherit = 'mrp.repair'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        """ enlever le menu du rapport par défaut.  """
        res = super(MrpRepair, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        report_quotation = self.env.ref(
                'mrp_repair.action_report_mrp_repair_order')
        #_logger.error("report_quotation : %s", report_quotation)
        #_logger.error("report_quotation xml_id : %s", report_quotation.xml_id)
        #_logger.error("report_quotation id : %s", report_quotation.id)

        #view_id = self.env['ir.model.data'].xmlid_to_res_id('mrp_repair.action_report_mrp_repair_order')
        #_logger.error("VIEW ID 1 : %s", view_id)

        #_logger.error("res toolbar print : %s", res['toolbar']['print'])
        for print_submenu in res.get('toolbar', {}).get('print', []):
            #_logger.error("print submenu : %s", print_submenu)
            if print_submenu['id'] == report_quotation.id:
                res['toolbar']['print'].remove(print_submenu)

        return res

    start_date = fields.Datetime('Start Date')
    duration = fields.Datetime('Duration')
    end_date = fields.Date(string="End Date", store=True,
                           compute='_get_end_date', inverse='_set_end_date')

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            start = fields.Datetime.from_string(r.start_date)
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = start + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            start_date = fields.Datetime.from_string(r.start_date)
            end_date = fields.Datetime.from_string(r.end_date)
            r.duration = (end_date - start_date).days + 1

class ReparationEvent(models.Model):
    _inherit = "calendar.event"

    reparation_id = fields.Many2one('mrp.repair')

    start_date = fields.Datetime('Start Date')

     
