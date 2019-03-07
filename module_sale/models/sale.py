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
sys.path.insert(0, '/mnt/extra-addons/')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    name = fields.Html(string='Description', required=True, default_focus=True)

    @api.multi
    def _prepare_invoice_line(self, qty):
        # print "[%s] sale.order.line our _prepare_invoice_line" % __name__

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
    def _create_invoice(self, order, so_line, amount):
        """
        override the function is necessary because we need to add the bl lines before the creation of the invoice
        """
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            prop_id = prop and prop.id or False
            account_id = order.fiscal_position_id.map_account(prop_id)
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') % \
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')

        bl_lines = []

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, [x.id for x in self.product_id.taxes_id])],
                'account_analytic_id': order.project_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
        })
        invoice.compute_taxes()

        for bl_line in order.picking_ids:
            # we list all the product user in the invoice and the current bl
            bl_line_products = [y.id for y in [z.product_id for z in bl_line.pack_operation_product_ids]]
            inv_line_products = [x.id for x in [w.product_id for w in invoice.invoice_line_ids]]

            same_product = False

            # if one of the bl product matches one from invoice, we add the bl to the bl list
            for bl_product in bl_line_products:
                if bl_product in inv_line_products:
                    same_product = True
                    break

            if same_product and bl_line.picking_type_id.code == 'outgoing':
                bl_lines.append(
                    self.env['bl.line'].create({'invoice_id': invoice.id, 'bl_id': bl_line.id, 'to_print': True}).id)

        invoice.update({'bl_line_ids': [(6, 0, bl_lines)]})

        return invoice

    @api.multi
    def create_invoices(self):
        """
            override the function is necessary because we need to change the bl lines before the return in some cases
        """
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        ret = {}

        if self.advance_payment_method == 'proforma':
            for order in sale_orders:
                for line in order.order_line:
                    line.qty_to_invoice = line.product_uom_qty

            inv_ids = sale_orders.action_invoice_create(final=True)
            for invoice in self.env['account.invoice'].browse(inv_ids):
                invoice.state = 'proforma2'
        elif self.advance_payment_method == 'delivered':
            created_invoices = sale_orders.action_invoice_create()

            invs = self.env["account.invoice"].search([('id', 'in', created_invoices)])

            # for each new invoice, we get sale orders of origin
            for inv in invs:
                bl_lines = []
                sos_name = inv.origin.split(", ")
                sos = self.env["sale.order"].search([('name', '=', sos_name)])

                # for each sale order of origin, we get related bls
                for so in sos:
                    for bl_line in so.picking_ids:
                        # we list all the product user in the invoice and the current bl
                        bl_line_products = [y.id for y in [z.product_id for z in bl_line.pack_operation_product_ids]]
                        inv_line_products = [x.id for x in [w.product_id for w in inv.invoice_line_ids]]

                        same_product = False

                        # if one of the bl product matches one from invoice, we add the bl to the bl list
                        for bl_product in bl_line_products:
                            if bl_product in inv_line_products:
                                same_product = True
                                break

                        if same_product and bl_line.picking_type_id.code == 'outgoing':
                            bl_lines.append(self.env['bl.line'].create({'invoice_id': inv.id, 'bl_id': bl_line.id, 'to_print': True}).id)

                inv.update({'bl_line_ids': [(6, 0, bl_lines)]})

        elif self.advance_payment_method == 'all':
            created_invoices = sale_orders.action_invoice_create(final=True)

            invs = self.env["account.invoice"].search([('id', 'in', created_invoices)])

            # for each new invoice, we get sale orders of origin
            for inv in invs:
                bl_lines = []
                sos_name = inv.origin.split(", ")
                sos = self.env["sale.order"].search([('name', '=', sos_name)])

                # for each sale order of origin, we get related bls
                for so in sos:
                    for bl_line in so.picking_ids:
                        # we list all the product user in the invoice and the current bl
                        bl_line_products = [y.id for y in [z.product_id for z in bl_line.pack_operation_product_ids]]
                        inv_line_products = [x.id for x in [w.product_id for w in inv.invoice_line_ids]]

                        same_product = False

                        # if one of the bl product matches one from invoice, we add the bl to the bl list
                        for bl_product in bl_line_products:
                            if bl_product in inv_line_products:
                                same_product = True
                                break

                        if same_product and bl_line.picking_type_id.code == 'outgoing':
                            bl_lines.append(self.env['bl.line'].create({'invoice_id': inv.id, 'bl_id': bl_line.id, 'to_print': True}).id)

                inv.update({'bl_line_ids': [(6, 0, bl_lines)]})
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting',
                                                         self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_(
                        'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_(
                        "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, self.product_id.taxes_id.ids)],
                })
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def create_invoice(self, order, so_line, amount):
        fpos = order.fiscal_position_id or order.partner_id.property_account_position_id
        account_env = self.env['account.account']
        partner_company_id = order.partner_id.company_id.id
        product_acct = self.product_id.sudo().property_account_income_id
        account_id = account_env.search([('code', '=', product_acct.code), ('company_id', '=', partner_company_id)])

        if fpos:
            account_id = fpos.map_account(account_id)

        res = super(SaleAdvancePaymentInvoice, self)._create_invoice(order, so_line, amount)
        res["invoice_line_ids"].account_id = account_id

        for line in res.invoice_line_ids:
            ids = fpos.map_tax(order.so_line.taxes_id).ids
            line.invoice_line_tax_ids = ids
            line._set_taxes()

        return res


from openerp.exceptions import UserError

class WizClientBlocked(models.TransientModel):
    _name = 'wiz_client_blocked'

error_client_blocked = """Attention, le client que vous sélectionnez est marqué comme 'bloqué' par la direction.
Merci de contacter la direction pour le faire débloquer. """

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    def _default_commercial(self):
        if not self.contact_affaire:
            return self.env.user

    contact_affaire = fields.Many2one('res.users', string='V/Contact affaire', default=_default_commercial)

    contact = fields.Many2one('res.partner', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    tuto = fields.Boolean(string="Formation incluse")
    install = fields.Boolean(string="Installation incluse")
    installation = fields.Selection(string="Installation incluse", selection=[(1, 'Non Incluse'), (2, 'Incluse'), (3, 'Sans Objet')])
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

        if self.partner_id.blocked:
            return {
                'warning': {'title': 'Attention', 'message': error_client_blocked},
            }


class AccountInvoiceInherited(models.Model):
    _inherit = "account.invoice"

    bl_line_ids = fields.One2many("bl.line", "invoice_id", string="Bons de livraison")

    @api.onchange('partner_id')
    def onchange_partner_id_2(self):
        super(AccountInvoiceInherited, self)._onchange_partner_id()

        if self.partner_id.blocked :
            return {
                'warning': {'title': 'Attention', 'message': error_client_blocked},
            }

    # This method is preparing lines to be shown on the printed invoice. The only goal is to be able to link the
    # invoice lines to the related delivery and display them grouped by deliveries (which means to split some
    # invoice lines sometimes
    def get_lines(self):
        involved_deliveries = []
        delivery_lines_unfiltered = []
        delivery_lines_unsorted = []
        delivery_lines_formated = []
        invoice_lines_formated = []
        combined_list = []

        # We need to make sure some deliveries are linked to this invoice
        if self.bl_line_ids:

            # if we found some delivery in the invoice header we collect the object.
            print('\n//////////////////////////////// DELIVERIES ///////////////////////////////////////////')
            print(self.bl_line_ids)
            for delivery in self.bl_line_ids:
                involved_deliveries.append(delivery.bl_id)

            # and then we look at their lines
            for delivery in involved_deliveries:
                for record in delivery.pack_operation_product_ids:
                    delivery_lines_unfiltered.append([delivery, record])

            # Now we can build a kind of invoice lines using on those delivery lines. But we'll have to make sure
            # that all the invoice lines and only the invoice lines are in, or add/remove what's necessary

            # step 1: format the delivery lines in an exploitable format
            for delivery_line in delivery_lines_unfiltered:
                delivery_lines_unsorted.append({
                                                'my_key': delivery_line[0].id,
                                                'invoice_line': '',
                                                'delivery': delivery_line[0],
                                                'delivery_line': delivery_line[1],
                                                'product': delivery_line[1].product_id,
                                                'qty': delivery_line[1].qty_done,
                                                'uom': delivery_line[1].product_uom_id
                })

        delivery_lines_formated = sorted(delivery_lines_unsorted, key=lambda k: k['my_key'], reverse=True)

        print('\n///////////////////////////// delivery_lines_formated and sorted //////////////////////')
        for bidule in delivery_lines_formated:
            print('my_key : %s - delivery : %s - item : %s - qty : %s'
                  % (bidule['my_key'], bidule['delivery'].name, bidule['product'].name, bidule['qty']))

        # step 2:  format the invoice lines in an exploitable format
        for invoice_line in self.invoice_line_ids:
            invoice_lines_formated.append({
                                           'my_key': 999999999,
                                           'invoice_line': invoice_line,
                                           'delivery': '',
                                           'delivery_line': '',
                                           'product': invoice_line.product_id,
                                           'qty': invoice_line.quantity,
                                           'uom': invoice_line.uom_id})

        print('\n//////////////////////////////// invoice_lines_formated ///////////////////////')
        for bidule in invoice_lines_formated:
            print('Item : %s - Qty : %s' % (bidule['product'].name, bidule['qty']))

        # And now, the goal is to compare and merge the two lists. Most important is that all invoice lines arrive
        # on the report, and only them. By consequence that will be our starting point.

        for invoice_item in invoice_lines_formated:
            print('\n\n---------------------- current invoice line to be match -----------------------')
            print('Invoice item : %s - qty : %s' % (invoice_item['product'].name, invoice_item['qty']))
            print('\n------------- Check delivery --------------------------------------------------')
            if invoice_item['qty'] > 0:
                for delivery_item in delivery_lines_formated:

                    print('Delivery : %s - Item : %s - Qty : %s'
                          % (delivery_item['delivery'].name, delivery_item['product'].name, delivery_item['qty']))

                    if delivery_item['qty'] > 0 and invoice_item['qty'] > 0:
                        if invoice_item['product'] == delivery_item['product']:
                            # We keep the most interesting field's value from both lines
                            temp_best_of_both = {
                                                'my_key': delivery_item['my_key'],
                                                'invoice_line': invoice_item['invoice_line'],
                                                'delivery': delivery_item['delivery'],
                                                'delivery_line': delivery_item['delivery_line'],
                                                'product': delivery_item['product'],
                                                'qty': delivery_item['qty'],
                                                'uom':  delivery_item['uom']}
                            combined_list.append(temp_best_of_both)
                            print('                            ............... This was the match ................')
                            if delivery_item['qty'] <= invoice_item['qty']:
                                invoice_item['qty'] -= delivery_item['qty']
                                delivery_item['qty'] = 0
                            else:
                                delivery_item['qty'] -= invoice_item['qty']
                                invoice_item['qty'] = 0

        # and finally we add potential remaining invoice lines that have not been matched to any delivery.
        # This can be all if no delivery at all was found.

        print('\n///////////////// REMAINING INVOICE LINES NOT MATCHED //////////////////////////')
        for invoice_item in invoice_lines_formated:
            if invoice_item['qty'] > 0 or invoice_item['product'].default_code == 'ACPT':
                print('Invoice item : %s - qty : %s' % (invoice_item['product'].name, invoice_item['qty']))

                combined_list.append(invoice_item)

        # But before returning the list, to make the qWeb step easier,  we reformat it
        # by grouping item lines by delivery:
        the_list = []
        unique_keys = []

        # step 1: make a list of delivery's header (including no delivery related key 999999999) and remove duplicates
        for record in combined_list:
            unique_keys.append(record['my_key'])
        unique_keys = list(set(unique_keys))
        unique_keys.sort(reverse=False)
        print('\n***************************** LIST OF UNIQUE KEYS ******************************')
        print(unique_keys)

        # step 2: using the unique delivery number as key, push the related item details lists:
        for one_key in unique_keys:
            temp2 = []
            pool_of_delivery = []
            for record in combined_list:
                if record['my_key'] == one_key:
                    pool_of_delivery.append(record)
            temp2.append(one_key)
            temp2.append(pool_of_delivery)
            the_list.append(temp2)
        print('\n***************************** LIST WITH ITEMS GROUPED BY DELIVERY **************')
        for machin in the_list:
            for chose in machin[1]:
                if chose['delivery']:
                    print('Delivery Number : %s - Item : %s - Qty : %s'
                          % (chose['delivery'].name, chose['product'].name, chose['qty']))
                else:
                    print('Delivery Number : no delivery - Item : %s - Qty : %s'
                          % (chose['product'].name, chose['qty']))
        print('\n')
        return the_list


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

