# -*- coding: utf-8 -*-
from openerp import http

from openerp import SUPERUSER_ID
from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

import openerp
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.addons.website_sale.controllers.main import QueryURL

from openerp.addons.report.controllers.main import ReportController

import pprint
pp = pprint.PrettyPrinter(indent=2)

class SalesController(ReportController):

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        print "[%s] our report_download" % __name__

        res = super (SalesController, self).report_download(data=data, token=token)
        print "res is : ", res
        pp.pprint(res)
        return res

