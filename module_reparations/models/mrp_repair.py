# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
import logging 

_logger = logging.getLogger(__name__)

class MrpRepair(models.Model):
    _inherit = 'mrp.repair'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """ enlever le menu du rapport par défaut.  """

        res = super(MrpRepair, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if not res.get('toolbar', {}).get('print', []):
            #_logger.error('print menu empty, returning unaltered view.')
            return res

        #view_id = self.env['ir.model.data'].xmlid_to_res_id('mrp_repair.action_report_mrp_repair_order')
        report_quotation = self.env.ref('mrp_repair.action_report_mrp_repair_order')

        #_logger.error("report_quotation xml_id : %s", report_quotation.xml_id)
        #_logger.error("Report Quotation ID is : %s ", report_quotation.id)

        res['toolbar']['print'] = [dict(t) for t in res.get('toolbar', {}).get('print', []) if t['id'] != report_quotation.id]

        return res 

    # not visible to the model until created, but exists in db
    create_date = fields.Datetime('Create Date', readonly=True)

    #duration = fields.Datetime('Durée de la réparation', compute='_get_duration')
    #duration = fields.Char('Durée de la réparation', compute='_get_duration')

    date_start = fields.Datetime(string='Date de début', required=True, store=True, index=True, copy=False, default=fields.Datetime.now, help="Date du début de la réparation")

    #end_date = fields.Datetime(string="End Date", required=True, store=True, compute='_get_end_date', inverse='_set_end_date', help="Date prévue de la fin de la réparation")
    end_date = fields.Datetime(string="Date de fin", required=True, store=True, help="Date prévue de la fin de la réparation")

"""
    @api.depends('date_start', 'end_date')
    def _get_duration(self):
        for r in self:
            if not (r.date_start and r.end_date):
                _logger.warning("date_start and end_date not set for record, duration set to 0")
                r.duration = 0
                continue
            start = fields.Datetime.from_string(r.date_start)
            end = fields.Datetime.from_string(r.end_date)
            r.duration = self.secs_to_char((end - start).seconds)

    def secs_to_char(self, seconds):
        """ takes seconds, returns formatted string hours:minutes """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        s = "%d:%02d" % (h, m)
        _logger.warning("returning time : %s", s)
        return s

    def char_to_td(self):
        """ takes char, returns timedelta """
        pass

"""

