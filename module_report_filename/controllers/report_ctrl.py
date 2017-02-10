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
        print "[%s] our report_download"
        #order_obj = http.request.env['sale.order']
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        reports_list = ['module_reparations.report_repair_devis',
                        'module_reparations.report_no_prices',
                        'module_sale.report_mysaleorder',
                        'module_purchase.report_mypurchaseorder']
        
        to_rename = False
        for report in reports_list :
            if report in data :
                to_rename = True

        if not to_rename :
            #_logger.error("Report not listed for rename, returning.")
            #_logger.error("data received was : %s", data)
            return ReportController().report_download(data, token)

        requestcontent = json.loads(data)
        url, typ = requestcontent[0], requestcontent[1]
        # reportname = u'sale.report_saleorder/37'
        reportname = url.split('/report/pdf/')[1].split('?')[0]
        reportname, doc_id = reportname.split('/')

        # get report object and model object. And document object (?) need it for the id
        report = request.registry['report']._get_report_from_name(cr, uid, reportname)
        model_obj = http.request.env[report.model]
        doc_obj = model_obj.browse(int(doc_id))

        # doc_obj.name is Sequence
        filename = report.name.replace(' ','-') + '-' + doc_obj.name
        print "filename of downloaded report will be : ", filename
        #_logger.error("Filename is : %s", filename)

        response = ReportController().report_download(data, token)
        response.headers.set('Content-Disposition', 'attachment; filename=%s.pdf;' % filename)
        return response

