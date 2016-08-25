# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
import logging 

_logger = logging.getLogger(__name__)

class ReportMask(object):

    def __init__(self, report_list):
        """ report_list is the LIST of report NAMES. means, their full ids
        example : ['module_purchase.report_mypurchaseorder'] """
        self.report_list = report_list

    def fields_view_get_masked(self, res, obj):
        
        #_logger.warning("fiels_view_get_masked here")
        if not res:
            raise Exception("No res received in fields_view_get_masked, in %s", __name__)

        #_logger.error('Purchase Order Fields View Get')
        if not res.get('toolbar', {}).get('print', []):
            #_logger.error('print menu empty, returning unaltered view.')
            return res

        report_id_list = []
        for report in self.report_list:
            report_id_list.append(obj.env['report']._get_report_from_name(report).id)

        res['toolbar']['print'] = [dict(t) for t in res.get('toolbar', {}).get('print', []) if t['id'] in report_id_list]

        return res 

