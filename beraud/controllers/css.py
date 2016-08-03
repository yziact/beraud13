# -*- coding: utf-8 -*-

import json
import time
import logging
import werkzeug
import werkzeug.utils
from datetime import datetime
from math import ceil

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.exceptions import UserError
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DTF, ustr


class CssInterface(http.Controller):
    @http.route(['/beraud/dynamic_backend.css'], type='http')
    def get_css(self, **post):
        user = http.request.env['res.users'].search([('id','=',request.session.uid)])

        if not user:
            return ''

        else:
            company_background_color = user.company_id.background_color or 'black'
            company_border_color = user.company_id.border_color or 'black'

            css_data = '.navbar-inverse { background-color: '+ company_background_color + '; border-color: '+ company_border_color + '; }' \
                    ' .o_web_client {background-color: #333333;} '

            return request.make_response(css_data, [('Content-Type', 'text/css')])

