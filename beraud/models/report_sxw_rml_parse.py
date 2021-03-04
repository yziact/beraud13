# -*- coding: utf-8 -*-
from lxml import etree
import StringIO
import cStringIO
import base64
from datetime import datetime
import os
import re
import time
import logging
import openerp.tools as tools
import zipfile
from openerp.exceptions import AccessError

import openerp
from openerp.report import preprocess
from openerp.report.interface import report_rml

from openerp import SUPERUSER_ID
from openerp.osv.fields import float as float_field, function as function_field, datetime as datetime_field
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.safe_eval import safe_eval as eval

from openerp.osv import osv
from openerp.report import report_sxw
from openerp.addons.mrp.report.bom_structure import bom_structure
from openerp.addons.mrp.report.bom_structure import report_mrpbomstructure

from openerp.report.report_sxw import rml_parse
from openerp.report.report_sxw import rml_parents
from openerp.report.report_sxw import rml_tag

class bom_structure_inherited(bom_structure):

    def __init__(self, cr, uid, name, context):
        if not context:
            context={}
        self.cr = cr
        self.uid = uid
        self.pool = openerp.registry(cr.dbname)
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        self.localcontext = {
            'user': user,
            'setCompany': self.setCompany,
            'repeatIn': self.repeatIn,
            'setLang': self.setLang,
            'setTag': self.setTag,
            'removeParentNode': self.removeParentNode,
            'format': self.format,
            'formatLang': self.formatLang,
            #'lang' : user.company_id.partner_id.lang,
            'translate' : self._translate,
            'setHtmlImage' : self.set_html_image,
            'strip_name' : self._strip_name,
            'time' : time,
            'display_address': self.display_address,
            # more context members are setup in setCompany() below:
            #  - company_id
            #  - logo
        }
        self.setCompany(user.company_id)
        self.localcontext.update(context)
        self.name = name
        self._node = None
        self.parents = rml_parents
        self.tag = rml_tag
        self._lang_cache = {}
        self.lang_dict = {}
        self.default_lang = {}
        self.lang_dict_called = False
        self._transl_regex = re.compile('(\[\[.+?\]\])')
        self.localcontext.update({
            'get_children': self.get_children,
        })

class report_mrpbomstructure(osv.AbstractModel):
    _name = 'report.mrp.report_mrpbomstructure'
    _inherit = 'report.abstract_report'
    _template = 'mrp.report_mrpbomstructure'
    _wrapped_report_class = bom_structure_inherited

