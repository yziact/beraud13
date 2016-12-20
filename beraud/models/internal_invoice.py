# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
import datetime

class Internal_Invoice(models.Model):
    _name = "beraud.invoice"

    date = fields.Date(string="Date fin")

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
        sale_invoice._onchange_partner_id()
        return sale_invoice

    @api.model
    def create_line_ids_for_goods(self, list, price_list_id, partner_id, company_id, invoice, type, journal_id):
        invoice_line_env = self.env['account.invoice.line']
        account_env = self.env['account.account']
        partner_env = self.env['res.partner']

        # fpos = invoice.partner_id.property_account_position_id.id
        list_line_ids = []
        for item in list:
            price_unit = item.product_id.tarif

            if type == 'out_invoice':
                prod_code = item.product_id.property_account_income_id.code[:-2] + "10"
                account_id = account_env.search([('code', '=', prod_code), ('company_id', '=', company_id)])
                if not account_id:
                    account_id = item.product_id.property_account_income_id
            else:
                prod_code = (item.product_id.property_account_expense_id.code[:-2] + "10")

                account_id = account_env.search([('code', '=', prod_code),
                                                 ('company_id', '=', company_id)])
                if not account_id:
                    account_id = item.product_id.property_account_expense_id

            line = invoice_line_env.create({'origin': 'internal',
                                            'create_date': datetime.date.today(),
                                            'price_unit': price_unit,
                                            'partner_id': partner_id,
                                            'company_id': company_id,
                                            'account_id': account_id.id,
                                            'uom_id': item.product_uom.id,
                                            'name': item.product_id.name,
                                            'product_id': item.product_id.id,
                                            'invoice_id': invoice.id,
                                            'quantity': item.product_qty,
                                            'move_id': item.id,
                                            })
            line._set_taxes()
            line.update({'price_unit': price_unit})
            # line._onchange_product_id()
            # print line
            # print "ACCOUNT LINE 2   :    ", line['account_id'].code
            # line['price_unit'] = price_unit
            list_line_ids.append(line)
        return list_line_ids

    @api.model
    def create_line_ids_for_timesheet(self, list, partner_id, company_id, invoice, type, journal_id):
        invoice_line_env = self.env['account.invoice.line']
        account_env = self.env['account.account']
        partner_env = self.env['res.partner']

        list_line_ids = []

        for item in list:
            price_unit = item['product'].tarif

            if type == 'out_invoice':
                prod_code = item['product'].property_account_income_id.code[:-2] + "10"
                account_id = account_env.search([('code', '=', prod_code), ('company_id', '=', company_id)])

                if not account_id:
                    account_id = item['product'].property_account_income_id

            else:
                prod_code = (item['product'].property_account_expense_id.code[:-2] + "10")
                account_id = account_env.search([('code', '=', prod_code), ('company_id', '=', company_id)])
                if not account_id:
                    account_id = item['product'].property_account_expense_id

            line = invoice_line_env.create({'origin': 'internal',
                                            'create_date': datetime.date.today(),
                                            'partner_id': partner_id,
                                            'company_id': company_id,
                                            'account_id': account_id.id,
                                            'invoice_id': invoice.id,
                                            'price_unit': price_unit,
                                            'timesheet_id': item['timesheet_id'],
                                            'product_id': item['product'].id,
                                            'uom_id': item['product'].product_tmpl_id.uom_id.id,
                                            'name': item['name'],
                                            'quantity': item['quantity']
                                            })
            line._set_taxes()
            line.update({'price_unit': price_unit})
            # line._onchange_product_id()
            # line.write({'name': item['name']})

            list_line_ids.append(line)

        return list_line_ids

    def get_move(self, list_move):
        list_ber = []
        list_atom = []
        for move in list_move:
            if move.partner_id.company_id.id == 3:
                list_ber.append(move)

            elif move.partner_id.company_id.id == 1:
                list_atom.append(move)

        return list_ber, list_atom

    def get_task(self, projet_line_task):
        print 'IN GET TASK'
        time_ber = []
        time_atom = []

        for line in projet_line_task:
            repair_env = self.env['mrp.repair']
            prod_env = self.env['product.product']

            if line.user_id.company_id.id != line.task_id.company_id.id:

                repair = repair_env.search([('task_id', '=', line.task_id.id)])
                if repair:

                    if repair.clientsite:

                        if line.user_id.company_id.id == 1:
                            product_time = prod_env.search([('default_code', '=', 'TBMOEX')])

                            time_ber.append({'quantity': line.unit_amount,
                                             'product': product_time,
                                             'name': (line.user_id.name + " : " +repair.name + " " + line.name ),
                                             'timesheet_id': line.id,
                                             })

                        if line.user_id.company_id.id == 3:
                            product_time = prod_env.search([('default_code', '=', 'TAMOEX')])

                            time_atom.append({'quantity': line.unit_amount,
                                              'product': product_time,
                                              'name': (line.user_id.name + " : " +repair.name + " " + line.name ),
                                              'timesheet_id': line.id,
                                              })
                    else:

                        if line.user_id.company_id.id == 1:
                            product_time = prod_env.search([('default_code', '=', 'TBMO')])

                            time_ber.append({'quantity': line.unit_amount,
                                             'product': product_time,
                                             'name': (line.user_id.name + " : " +repair.name + " " + line.name),
                                             'timesheet_id': line.id,
                                             })

                        if line.user_id.company_id.id == 3:
                            product_time = prod_env.search([('default_code', '=', 'TAMO')])

                            time_atom.append({'quantity': line.unit_amount,
                                              'product': product_time,
                                              'name': (line.user_id.name + " : " +repair.name + " " + line.name),
                                               'timesheet_id': line.id,
                                          })
                else:

                    if line.user_id.company_id.id == 1:
                        product_time = prod_env.search([('default_code', '=', 'TBMO')])

                        time_ber.append({'quantity': line.unit_amount,
                                         'product': product_time,
                                         'name': (line.user_id.name + " : " + line.name),
                                         'timesheet_id': line.id,
                                         })

                    if line.user_id.company_id.id == 3:
                        product_time = prod_env.search([('default_code', '=', 'TAMO')])

                        time_atom.append({'quantity': line.unit_amount,
                                          'product': product_time,
                                          'name': (line.user_id.name + " : " + line.name),
                                          'timesheet_id': line.id,
                                          })



        return time_ber, time_atom


    @api.multi
    def action_create_internal_invoice(self):
        date = self.date
        self.sudo().create_internal_invoice(date)

    @api.model
    def create_internal_invoice(self, date):
        # Variables d'environemment :
        partner_env = self.env['res.partner']
        moves_env = self.env['stock.move']
        journal_env = self.env['account.journal']
        analytic_line_env = self.env['account.analytic.line']

        # List des mouvements
        list_ber = []
        list_atom = []
        time_ber = []
        time_atom = []
        sale_line_ids = []
        sale_invoice = False

        # On ne cherche que les mouvements non factures
        moves = moves_env.search([('billed', '=', False), ('isSale', '=', True), ('date', '<=', date)])

        # On ne cherche que les account line liee a un projet
        projet_line_task = analytic_line_env.search([('billed', '=', False), ('task_id', '!=', False), ('date', '<=', date)])


        # projet_line_issue = analytic_line_env.search([('billed', '=', False), ('issue_id', '!=', False), ('date', '<=', date)])

        # On repartit les mouvements de ventes dans chaque list:

        list_ber, list_atom = self.get_move(moves)
        time_ber, time_atom = self.get_task(projet_line_task)


#         for line in projet_line_issue:
#             product_time = prod_env.search([('default_code', '=', 'MO')])
#             if line.user_id.company_id.id != line.issue_id.company_id.id:
#                 time_ber.append({'quantity': line.unit_amount,
#                                  'product': product_time,
#                                  'name': line.name,
#                                  'timesheet_id': line.id,
#                                  })
#             if line.user_id.company_id.id == 3:
#                 time_atom.append({'quantity': line.unit_amount,
#                                   'product': product_time,
#                                   'name': line.name,
#                                   'timesheet_id': line.id,
#                                   })
#


 ### CAS FACTURE VENTE BERAUD

        #Test si il y a une liste de bien echangee de ber -> atom
        if len(list_ber) !=0:
            account_id = partner_env.browse([6]).with_context(company_id=1).property_account_receivable_id.id
            journal_id_sale = journal_env.search([('company_id', '=', 1), ('type', '=', 'sale')])[0].id

            sale_invoice = self.create_invoice(6,1, 'out_invoice', account_id, journal_id_sale)
            sale_line_ids_goods = self.create_line_ids_for_goods(list_ber, 5, 6, 1, sale_invoice, 'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_goods

        # Test si il y a une liste de temps a facturer de ber -> atom
        if len(time_ber) !=0:
            if not sale_invoice :
                account_id = partner_env.browse([6]).with_context(company_id=1).property_account_receivable_id.id
                journal_id_sale = journal_env.search([('company_id', '=', 1), ('type', '=', 'sale')])[0].id
                sale_invoice = self.create_invoice(6, 1, 'out_invoice', account_id, journal_id_sale)

            sale_line_ids_timesheet = self.create_line_ids_for_timesheet(time_ber, 6, 1, sale_invoice, 'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_timesheet



        if len(sale_line_ids) != 0:
            sale_invoice.compute_taxes()

            # creation de la facture jumelle cote achat
            account_id = partner_env.browse([1]).with_context(company_id=3).property_account_payable_id.id
            journal_id = journal_env.search([('company_id', '=', 3), ('type', '=', 'purchase')])[0].id

            purchase_invoice = self.create_invoice(1, 3, 'in_invoice', account_id, journal_id)
            purchase_line_ids = []

            if len(list_ber) != 0:
                purchase_line_ids_goods = self.create_line_ids_for_goods(list_ber, 5, 1, 3, purchase_invoice, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_goods

            if len(time_ber) != 0:
                purchase_line_ids_timesheet = self.create_line_ids_for_timesheet(time_ber, 1, 3, purchase_invoice, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_timesheet

            purchase_invoice.compute_taxes()

 ### CAS FACTURE VENTE ATOM
        sale_line_ids = []
        if len(list_atom) != 0:
            account_id = partner_env.browse([1]).with_context(company_id=3).property_account_receivable_id.id
            journal_id_sale = journal_env.search([('company_id', '=', 3), ('type', '=', 'sale')])[0].id

            sale_invoice = self.create_invoice(1, 3, 'out_invoice', account_id, journal_id_sale)
            sale_line_ids_goods = self.create_line_ids_for_goods(list_atom, 5, 1, 3, sale_invoice, 'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_goods

        if len(time_atom) != 0:
            if not sale_invoice:
                account_id = partner_env.browse([1]).with_context(company_id=3).property_account_receivable_id.id
                journal_id_sale = journal_env.search([('company_id', '=', 3), ('type', '=', 'sale')])[0].id
                sale_invoice = self.create_invoice(1, 3, 'out_invoice', account_id, journal_id_sale)

            sale_line_ids_timesheet = self.create_line_ids_for_timesheet(time_atom, 1, 3, sale_invoice, 'out_invoice', journal_id_sale)
            sale_line_ids += sale_line_ids_timesheet

        if len(sale_line_ids) != 0:
            sale_invoice.compute_taxes()

            # creation de la facture jumelle cote achat
            journal_id = journal_env.search([('company_id', '=', 1), ('type', '=', 'purchase')])[0].id
            account_id = partner_env.browse(6).with_context(company_id=1).property_account_payable_id.id
            purchase_invoice = self.create_invoice(6, 1, 'in_invoice', account_id, journal_id)
            purchase_line_ids = []

            if len(list_atom) != 0:
                purchase_line_ids_goods = self.create_line_ids_for_goods(list_atom, 5, 6, 1, purchase_invoice, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_goods

            if len(time_atom) != 0:
                purchase_line_ids_timesheet = self.create_line_ids_for_timesheet(time_atom, 6, 1, purchase_invoice, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_timesheet

            purchase_invoice.compute_taxes()


class inherit_AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    move_id = fields.Many2one("stock.move", help='link between the stock move and the invoice line')
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
