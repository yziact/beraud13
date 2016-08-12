from openerp.addons.web.http import Controller, route, request
from openerp.addons.report.controllers.main import ReportController
from openerp.osv import osv
from openerp import http
import json
import logging 

_logger = logging.getLogger(__name__)

class PTReportController(ReportController):

    @route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        #order_obj = http.request.env['sale.order']
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        # only for mrp_repair reports...
        #if ("beraud.report_repair_devis" not in data) and ("beraud.report_no_prices" not in data) :
        if (("module_reparations.report_repair_devis" not in data) and
                ("module_reparations.report_no_prices" not in data)) :
            #_logger.info("returning unaltered view")
            return ReportController().report_download(data, token)

        #_logger.error("cr is : %s ", cr)
        #_logger.error("data is : %s ", data)
        requestcontent = json.loads(data)
        order_obj = http.request.env['mrp.repair']

        #_logger.error("RQ of request : %s", requestcontent)
        #_logger.error("RQ[0] is : %s", requestcontent[0])
        #_logger.error("RQ[1] is : %s", requestcontent[1])
        
        url, typ = requestcontent[0], requestcontent[1]
        #url = '/report/pdf/mrp_repair.report_mrprepairorder/1?enable_editor=1'
        #type = 'qweb-pdf'
        #assert type == 'qweb-pdf'

        reportname = url.split('/report/pdf/')[1].split('?')[0]
        # reportname = u'sale.report_saleorder/37'
        reportname, doc_id = reportname.split('/')
        # reportname = u'sale.report_saleorder'
        # docids = 37
        #_logger.error("doc id is : %s", doc_id)
        #_logger.error("reportname is : %s", reportname)
        doc_obj = order_obj.browse(int(doc_id))

        # get name of report as it is displayed on the pdf
        report = request.registry['report']._get_report_from_name(cr, uid, reportname)
        #_logger.error("report.name is : %s", report.name)

        # doc_obj.name is Sequence
        filename = report.name + ' - ' + doc_obj.name
        #_logger.error("Filename is : %s", filename)

        response = ReportController().report_download(data, token)
        response.headers.set('Content-Disposition', 'attachment; filename=%s.pdf;' % filename)
        return response

