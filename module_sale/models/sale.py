# -*- coding: utf-8 -*-

from openerp import models, api, fields, _
from lxml import etree
import datetime
import sys
from utilsmod import utilsmod
import time
import logging
_logger = logging.getLogger(__name__)


sys.path.insert(0, '..')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud/')
sys.path.insert(0, '/var/lib/odoo/odoo-beraud2')




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    name = fields.Html(string='Description', required=True, default_focus=True)

    @api.multi
    def _prepare_invoice_line(self, qty):
        print "[%s] sale.order.line our _prepare_invoice_line" % __name__

        account_env = self.env['account.account']
        partner_company_id = self.order_id.partner_id.company_id.id
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        account_code = account_env.sudo().browse(res['account_id']).code
        account_id = account_env.search([('code', '=', account_code), ('company_id','=', partner_company_id)])

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account_id = fpos.map_account(account_id)

        res['account_id'] = account_id.id

        return res

class SaleAdvancePaymentInvoice(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    advance_payment_method = fields.Selection(selection_add=[('proforma', 'Proforma')])

    @api.multi
    def create_invoices(self):
        print "[%s] sale.advance.payment.inv our create_invoices" % __name__

        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        ret = {}

        if self.advance_payment_method == 'proforma':
            for order in sale_orders:
                for line in order.order_line:
                    line.qty_to_invoice = line.product_uom_qty

            inv_ids = sale_orders.action_invoice_create(final=True)
            for invoice in self.env['account.invoice'].browse( inv_ids ):
                invoice.state = 'proforma2'

            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()

            return {'type': 'ir.actions.act_window_close'}

        else:
            ret = super(SaleAdvancePaymentInvoice, self).create_invoices()
            return ret

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        print "[%s] sale.advance.payment.inv our _create_invoices" % __name__

        fpos = order.fiscal_position_id or order.partner_id.property_account_position_id
        account_env = self.env['account.account']
        partner_company_id = order.partner_id.company_id.id
        product_acct = self.product_id.sudo().property_account_income_id
        account_id = account_env.search([('code', '=', product_acct.code), ('company_id', '=', partner_company_id)])

        if fpos:
            account_id = fpos.map_account(account_id)

        res = super(SaleAdvancePaymentInvoice, self)._create_invoice(order, so_line, amount)
        res["invoice_line_ids"].account_id = account_id
        return res


from openerp.exceptions import UserError

class WizClientBlocked(models.TransientModel):
    _name = 'wiz_client_blocked'

error_client_blocked = """Attention, le client que vous sélectionnez est marqué comme 'bloqué' par la direction.
Merci de contacter la direction pour le faire débloquer. """

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    contact = fields.Many2one('res.partner', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    commercial = fields.Many2one('res.users', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    tuto = fields.Boolean(string="Formation incluse")
    install = fields.Boolean(string="Installation incluse")
    delay = fields.Char(string="Délai")
    reglement = fields.Many2one('reglement')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        mask = utilsmod.ReportMask(['module_sale.report_mysaleorder'])
        res = super(SaleOrderInherit, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return mask.fields_view_get_masked(res, self)

    @api.onchange('partner_id')
    def onchange_partner_id_2(self):
        super(SaleOrderInherit, self).onchange_partner_id()
        print "[%s] our onchange" % __name__
        if self.partner_id.blocked:
            print "partner is blocked"
            return {
                'warning': {'title': 'Attention', 'message': error_client_blocked},
            }


class AccountInvoiceInherited(models.Model):
    _inherit = "account.invoice"

    @api.onchange('partner_id')
    def onchange_partner_id_2(self):
        super(AccountInvoiceInherited, self)._onchange_partner_id()
        print "[%s] our onchange" % __name__
        if self.partner_id.blocked :
            print "partner is blocked"
            return {
                'warning': {'title': 'Attention', 'message': error_client_blocked},
            }


class Reglement(models.Model):
    _name = 'reglement'

    name = fields.Text('Description')


import pprint
pp = pprint.PrettyPrinter(indent=2)

import lxml.html


'''
class SaleReport(models.AbstractModel):
    #_name = 'report.module.report_name'
    _name = 'report.module_sale.report_mysaleorder'

    # called by the get_html function of reports
    @api.multi
    def render_html(self, data=None):
        print "[%s] our render_html" % __name__
        print "data : ", data
        #import pudb; pudb.set_trace()

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('module_sale.report_mysaleorder')
        print "report : ", report
        print "report.name : ", report.name
        print "report.report_name : ", report.report_name
        docargs = {
            #'doc_ids': self._ids,
            #'doc_model': report.model,
            #'docs': self,
            'doc_model': 'sale.order',
            'docs': self.env['sale.order'].browse(self._ids)
        }
        res = report_obj.render(report.report_name, docargs)
        #print "res is : "
        #pp.pprint(res)
        return res
'''

'''

from reportlab.pdfgen.canvas import Canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
from pdfrw.toreportlab import makerl
from pdfrw.buildxobj import pagexobj
from pdfrw.buildxobj import pagexobj

from reportlab.lib.units import inch

from functools import partial
#from openerp.addons.report.models.report import Report

class ReportInherited(models.Model):
    _inherit = "report"

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None, context=None):
        print "[%s] our get_pdf" % __name__

        if html is None:
            html = self.get_html(cr, uid, ids, report_name, data=data, context=context)

        #print "HTML is : "
        #pp.pprint(html)

        #html = html.decode('utf-8')  # Ensure the current document is utf-8 encoded.

        # stuff to get the base_url
        irconfig_obj = self.pool['ir.config_parameter']
        base_url = irconfig_obj.get_param(cr, 1, 'report.url') or irconfig_obj.get_param(cr, 1, 'web.base.url')

        # Minimal page renderer
        view_obj = self.pool['ir.ui.view']
        render_minimal = partial(view_obj.render, cr, uid, 'report.minimal_layout', context=context)

        second_header = []
        root = lxml.html.fromstring(html)

        cart = lxml.html.tostring(root.xpath('//table')[0])
        cart_minimal = render_minimal(dict(subst=True, body=cart, base_url=base_url))
        #print "cart through render_minimal : ", render_minimal(dict(subst=True, body=cart, base_url=base_url))

        report = self._get_report_from_name(cr, uid, report_name)
        # Get the paperformat associated to the report, otherwise fallback on the company one.
        if not report.paperformat_id:
            user = self.pool['res.users'].browse(cr, uid, uid)
            paperformat = user.company_id.paperformat_id
        else:
            paperformat = report.paperformat_id

        # Get paperformat arguments set in the root html tag. They are prioritized over
        # paperformat-record arguments.
        specific_paperformat_args = {}
        for attribute in root.items():
            if attribute[0].startswith('data-report-'):
                specific_paperformat_args[attribute[0]] = attribute[1]

        #cart_pdf = super(ReportInherited, self).get_pdf(cr, uid, ids, "rando_report", cart_minimal, None, None)
        #cart_pdf = super(ReportInherited, self)._run_wkhtmltopdf(
        cart_pdf = self._run_wkhtmltopdf(cr, uid, [], [], [(42, cart)], False, paperformat, specific_paperformat_args)
        cart_file = '/tmp/cart.tmp.pdf'
        with open(cart_file, 'wb') as outfile:
            outfile.write(cart_pdf)

        #print "cart_pdf : ", cart_pdf

        #for node in root.xpath("//table"):
            # body = lxml.html.tostring(node)
            # print "body : ", body
            # header = render_minimal(dict(subst=True, body=body, base_url=base_url))
            # print "header : ", header
            # second_header.append(header)

        res = super(ReportInherited, self).get_pdf(cr, uid, ids, report_name, html, data, context)
        
        # if the report isn't the sale report, we don't need to further modify it.
        if report_name != "module_sale.report_mysaleorder":
            return res

        tmp_file = "/tmp/report_tmp.pdf"
        out_file = "/tmp/new_report.pdf"

        # need to write the pdf to disk first, cause pdfrw works that way
        # tmp_file hold the report we want to modify
        f = open(tmp_file, 'wb')
        f.write(res)
        f.close()

        # Get pages
        #reader = PdfReader(input_file)
        reader = PdfReader(tmp_file)
        wmark_reader = PdfReader(cart_file)
        wmark_page = wmark_reader.pages[0]

        pages = [pagexobj(p) for p in reader.pages]
        canvas = Canvas(out_file)
        #p_add = pagexobj(PdfReader(cart_file, decompress=False).pages[0])

        #compose a new pdf
        for page_num, page in enumerate(reader.pages, 1):
            if page_num == 1 :
                continue
            mbox = tuple(float(x) for x in page.MediaBox)
            page_x, page_y, page_x1, page_y2 = mbox
            # Create a new watermark object.
            wmark = PageMerge().add(wmark_page, viewrect=(0, 0.1, 1, 0.1))[0]
            wmark.scale(0.6, 0.6)
            # (0,0) is bottom left
            wmark.x = 15 
            wmark.y = 725
            # Add the watermark to the page
            PageMerge(page).add(wmark).render()

        # Write out the destination file
        PdfWriter().write(out_file, reader)

        # open and return
        f = open(out_file)
        return f.read()

        #for page_num, page in enumerate(pages):
            #print "page_num : ", page_num
            # Add page
            #canvas.setPageSize((page.BBox[2], page.BBox[3]))
            #canvas.doForm(makerl(canvas, page))

            #rl_page = makerl(canvas, page)
            #print "rl_page : ", rl_page
            #canvas.doForm(rl_page)
'''

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    blocked = fields.Boolean(default=False, string=u'Bloqué')

