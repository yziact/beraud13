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

        _logger.error("http context is : %s ", http.request.context)

        _logger.error("cr is : %s ", cr)
        _logger.error("data is : %s ", data)
        _logger.error("token is : %s ", token)
        requestcontent = json.loads(data)
        order_obj = http.request.env['mrp.repair']

        _logger.error("data of request : %s", data)
        _logger.error("type of data of request : %s", type(data))
        _logger.error("RQ of request : %s", requestcontent)
        _logger.error("RQ type of request : %s", type(requestcontent))
        _logger.error("RQ[0] is : %s", requestcontent[0])
        _logger.error("RQ[1] is : %s", requestcontent[1])
        
        url, typ = requestcontent[0], requestcontent[1]
        #url = '/report/pdf/mrp_repair.report_mrprepairorder/1?enable_editor=1'
        #type = 'qweb-pdf'
        #assert type == 'qweb-pdf'

        _logger.error("url is : %s", url)
        reportname = url.split('/report/pdf/')[1].split('?')[0]
        # reportname = u'sale.report_saleorder/37'
        reportname, doc_id = reportname.split('/')
        # reportname = u'sale.report_saleorder'
        # docids = 37
        #assert doc_id
        _logger.error("doc id is : %s", doc_id)
        _logger.error("reportname is : %s", reportname)
        doc_obj = order_obj.browse(int(doc_id))

        # get name of report as it is displayed on the pdf
        report = request.registry['report']._get_report_from_name(cr, uid, reportname)
        _logger.error("report.name is : %s", report.name)

        # doc_obj.name is Sequence
        filename = report.name + ' - ' + doc_obj.name
        _logger.error("Filename is : %s", filename)

        response = ReportController().report_download(data, token)
        response.headers.set('Content-Disposition', 'attachment; filename=%s.pdf;' % filename)
        return response

