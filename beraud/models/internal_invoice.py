# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class Internal_Invoice(models.Model):
    _name = "beraud.invoice"

    @api.model
    def create_invoice(self, partner_id, company_id, type, account_id, journal_id):
        invoice_env = self.env['account.invoice']
        sale_invoice = invoice_env.create({'origin': 'Internal',
                                           'type': type,
                                           'date_invoice': datetime.date.today(),
                                           'partner_id': partner_id,
                                           'company_id': company_id,
                                           'account_id': account_id,
                                           'journal_id': journal_id,
                                           })
        return sale_invoice

    @api.model
    def create_line_ids_for_goods(self, list, price_list_id, partner_id, company_id,invoice, account_id, type, journal_id):
        item_pricelist_env = self.env['product.pricelist.item']
        invoice_line_env = self.env['account.invoice.line']
        journal = self.env['account.journal'].browse(journal_id)
        list_line_ids = []

        for item in list:
            price_unit = item_pricelist_env.search([("pricelist_id", "=", price_list_id), ("product_id", "=", item.product_id.id)]).fixed_price
            if not price_unit :
                price_unit = item.product_id.tarif

            line = invoice_line_env.create({'origin': 'internal',
                                            'create_date': datetime.date.today(),
                                            'price_unit': price_unit,
                                            'partner_id': partner_id,
                                            'company_id': company_id,
                                            'account_id': account_id,
                                            'uom_id': item.product_uom.id,
                                            'name': item.product_id.name,
                                            'product_id': item.product_id.id,
                                            'invoice_id': invoice.id,
                                            'quantity': item.product_qty,
                                            'move_id': item.id,
                                            })
            line._set_taxes()
            line._onchange_product_id()
            if type == 'out_invoice':
                line.write({'account_id': journal.with_context(force_company=company_id).default_credit_account_id.id})
            else:
                line.write({'account_id': journal.with_context(force_company=company_id).default_debit_account_id.id})

            list_line_ids.append(line)
        return list_line_ids

    @api.model
    def create_line_ids_for_timesheet(self, list, partner_id, company_id, invoice, account_id, type, journal_id):
        invoice_line_env = self.env['account.invoice.line']
        journal = self.env['account.journal'].browse(journal_id)
        list_line_ids = []

        for item in list:
            line = invoice_line_env.create({'origin': 'internal',
                                            'create_date': datetime.date.today(),
                                            'partner_id': partner_id,
                                            'company_id': company_id,
                                            'account_id': account_id,
                                            'invoice_id': invoice.id,
                                            'price_unit': item['product'].product_tmpl_id.tarif,
                                            'timesheet_id': item['timesheet_id'],
                                            'product_id': item['product'].id,
                                            'uom_id': item['product'].product_tmpl_id.uom_id.id,
                                            'name': item['name'],
                                            'quantity': item['quantity']
                                            })
            line._set_taxes()
            line._onchange_product_id()
            line.write({'name': item['name']})
            if type == 'out_invoice':
                line.write({'account_id': journal.with_context(force_company=company_id).default_credit_account_id.id})
            else:
                line.write({'account_id': journal.with_context(force_company=company_id).default_debit_account_id.id})

            print line.account_id.company_id.id
            print line.company_id.id
            # print line.journal_id.company_id.id
            print line.invoice_id.company_id.id
            print invoice.company_id.id
            print invoice.journal_id.company_id.id

            list_line_ids.append(line)

        return list_line_ids

    @api.model
    def create_internal_invoice(self):
        # Variables d'environemment :
        partner_env = self.env['res.partner']
        moves_env = self.env['stock.move']
        journal_env = self.env['account.journal']
        analytic_line_env = self.env['account.analytic.line']
        prod_env = self.env['product.product']

        # List des mouvements
        list_ber = []
        list_atom = []
        time_ber = []
        time_atom = []
        sale_line_ids = []
        sale_invoice = False

        # On ne cherche que les mouvements non factures
        moves = moves_env.search([('billed', '=', False)])
        # On ne cherche que les account line liee a un projet
        projet_line_task = analytic_line_env.search([('billed', '=', False),('task_id', '!=', False)])
        projet_line_issue = analytic_line_env.search([('billed', '=', False), ('issue_id', '!=', False)])
        # On repartit les mouvements de ventes dans chaque list:
        for move in moves:
            if move.company_id.id == 1 and move.partner_id.id == 6 and move.isSale == True:
                list_ber.append(move)

            elif move.company_id.id == 3 and move.partner_id.id == 1 and move.isSale == True:
                list_atom.append(move)


        for line in projet_line_task:
            repair_env = self.env['mrp.repair']

            if line.user_id.company_id.id != line.task_id.company_id.id:
                repair = repair_env.search([('task_id', '=', line.task_id.id)])
                if repair:
                    if repair.clientsite:
                        product_time = prod_env.search([('default_code', '=', 'MOEX')])
                else:
                    product_time = prod_env.search([('default_code', '=', 'MO')])
                    if line.user_id.company_id.id == 1:
                        time_ber.append({'quantity':line.unit_amount,
                                         'product': product_time,
                                         'name':line.name,
                                         'timesheet_id': line.id,
                                         })
                    if line.user_id.company_id.id == 3:
                        time_atom.append({'quantity':line.unit_amount,
                                         'product': product_time,
                                         'name':line.name,
                                         'timesheet_id': line.id,
                                         })
        for line in projet_line_issue:
            product_time = prod_env.search([('default_code', '=', 'MO')])
            if line.user_id.company_id.id != line.issue_id.company_id.id:
                time_ber.append({'quantity': line.unit_amount,
                                 'product': product_time,
                                 'name': line.name,
                                 'timesheet_id': line.id,
                                 })
            if line.user_id.company_id.id == 3:
                time_atom.append({'quantity': line.unit_amount,
                                  'product': product_time,
                                  'name': line.name,
                                  'timesheet_id': line.id,
                                  })

### CAS FACTURE VENTE BERAUD
        #Test si il y a une liste de bien echangee de ber -> atom
        if len(list_ber) !=0:
            account_id = list_ber[0].partner_id.property_account_receivable_id.id
            journal_id_sale = journal_env.search([('company_id', '=', 1), ('type', '=', 'sale')])[0].id

            sale_invoice = self.create_invoice(6,1, 'out_invoice', account_id, journal_id_sale)
            sale_line_ids_goods = self.create_line_ids_for_goods(list_ber, 5, 6, 1, sale_invoice, account_id, 'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_goods

        # Test si il y a une liste de temps a facturer de ber -> atom
        if len(time_ber) !=0:
            if not sale_invoice :
                account_id = partner_env.browse([6]).property_account_receivable_id.id
                journal_id_sale = journal_env.search([('company_id', '=', 1), ('type', '=', 'sale')])[0].id
                sale_invoice = self.create_invoice(6, 1, 'out_invoice', account_id, journal_id_sale)

            sale_line_ids_timesheet = self.create_line_ids_for_timesheet(time_ber, 6, 1, sale_invoice, account_id,'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_timesheet



        if len(sale_line_ids) != 0:
            sale_invoice.compute_taxes()

            # creation de la facture jumelle cote achat
            journal_id = journal_env.search([('company_id', '=', 3), ('type', '=', 'purchase')])[0].id
            account_id = partner_env.browse(1).property_account_payable_id.id
            purchase_invoice = self.create_invoice(1, 3, 'in_invoice', account_id, journal_id)
            purchase_line_ids = []

            if len(list_ber) != 0:
                purchase_line_ids_goods = self.create_line_ids_for_goods(list_ber, 5, 1, 3, purchase_invoice, account_id, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_goods

            if len(time_ber) != 0:
                purchase_line_ids_timesheet = self.create_line_ids_for_timesheet(time_ber, 1, 3, purchase_invoice, account_id, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_timesheet

            purchase_invoice.compute_taxes()

### CAS FACTURE VENTE ATOM
        sale_line_ids = []
        if len(list_atom) != 0:
            account_id = list_atom[0].partner_id.property_account_receivable_id.id
            journal_id_sale = journal_env.search([('company_id', '=', 3), ('type', '=', 'sale')])[0].id

            sale_invoice = self.create_invoice(1, 3, 'out_invoice', account_id, journal_id_sale)
            sale_line_ids_goods = self.create_line_ids_for_goods(list_atom, 5, 1, 3, sale_invoice, account_id, 'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_goods

        if len(time_atom) != 0:
            if not sale_invoice:
                account_id = partner_env.browse([1]).property_account_receivable_id.id
                journal_id_sale = journal_env.search([('company_id', '=', 3), ('type', '=', 'sale')])[0].id
                sale_invoice = self.create_invoice(1, 3, 'out_invoice', account_id, journal_id_sale)

            sale_line_ids_timesheet = self.create_line_ids_for_timesheet(time_atom, 1, 3, sale_invoice, account_id, 'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_timesheet

        if len(sale_line_ids) != 0:
            sale_invoice.compute_taxes()

            # creation de la facture jumelle cote achat
            journal_id = journal_env.search([('company_id', '=', 1), ('type', '=', 'purchase')])[0].id
            account_id = partner_env.browse(6).property_account_payable_id.id
            purchase_invoice = self.create_invoice(6, 1, 'in_invoice', account_id, journal_id)
            purchase_line_ids = []

            if len(list_atom) != 0:
                purchase_line_ids_goods = self.create_line_ids_for_goods(list_atom, 5, 6, 1, purchase_invoice, account_id, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_goods

            if len(time_atom) != 0:
                purchase_line_ids_timesheet = self.create_line_ids_for_timesheet(time_atom, 6, 1, purchase_invoice, account_id, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_timesheet

            purchase_invoice.compute_taxes()


class inherit_AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    move_id  = fields.Many2one("stock.move", help='link between the stock move and the invoice line')
    timesheet_id = fields.Many2one("account.analytic.line", help='link between the time on a project move and the invoice line')


class inherit_AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            for invoice_line in invoice.invoice_line_ids:
                if invoice_line.move_id.id:
                    invoice_line.move_id.billed = True
                if invoice_line.timesheet_id.id:
                    invoice_line.timesheet_id.billed = True
        return super(inherit_AccountInvoice, self).invoice_validate()
class inherit_stock_move(models.Model):
    _inherit = 'stock.move'
    billed = fields.Boolean("Is billed", default=False)
    isSale = fields.Boolean(u"State move")
class inherit_analytic_line(models.Model):
    _inherit = 'account.analytic.line'
    billed = fields.Boolean("Is billed", default=False)
