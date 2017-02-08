# -*- Encoding: UTF-8 -*-

from openerp import models, api, fields
from datetime import datetime, date, time

class Internal_Invoice(models.Model):
    _name = "beraud.invoice"

    date = fields.Date(string="Date fin")

    @api.model
    def create_invoice(self, partner_id, company_id, type, account_id, journal_id):
        invoice_env = self.env['account.invoice']
        sale_invoice = invoice_env.create({'origin': 'Internal',
                                           'type': type,
                                           'date_invoice': date.today(),
                                           'partner_id': partner_id,
                                           'company_id': company_id,
                                           'account_id': account_id,
                                           'journal_id': journal_id,
                                           })
        sale_invoice._onchange_partner_id()
        return sale_invoice

    @api.model
    def create_line_ids_for_goods(self, list, price_list_id, partner_id, company_id, invoice, type, journal_id, date_borne):
        invoice_line_env = self.env['account.invoice.line']
        account_env = self.env['account.account']
        partner_env = self.env['res.partner']
        stock_pack_ope_lot_env = self.env['stock.pack.operation.lot']
        slist = sorted(list, key=lambda k: k['date'])

        list_line_ids = []
        for item in slist:
            price_unit = item.product_id.tarif
            name = item.product_id.display_name

            #Init variable pour info sur invoice_line
            date_move = ''
            origin_move = ''
            date_bl = ''
            serial = ''

            if not item.origin == 'TSIS move':
                origin_move = item.origin

                # Si le mouvement a un BL lier on recupere ses info
                if item.picking_id:
                    #seulement si la date du BL est inferieur a la borne, sinon on ne facture pas le mouvement ce mois si
                    if item.picking_id.date <= date_borne:
                        date_bl = datetime.strptime(item.picking_id.date.split(' ')[0], '%Y-%m-%d').strftime('%d-%m-%Y')

                    else:
                        continue

                date_bl = item.date

                if item.restrict_lot_id:
                    serial = item.restrict_lot_id.name

            else:
                #le mouvement est anterieur au 18 jan. on cherche les info via le num de serie
                if item.restrict_lot_id:
                    stock_pack_ope_lot_ids = stock_pack_ope_lot_env.search([('lot_id', '=', item.restrict_lot_id.id)])

                    serial = item.restrict_lot_id.name
                    pick_date = False
                    # on remonte au picking via les stock pack op
                    for pack in stock_pack_ope_lot_ids:
                        picking = pack.operation_id.picking_id

                        #si le type du picking est outgoing alors c est un BL client
                        if picking.picking_type_id.code == 'outgoing':
                            pick_date = picking.date
                            origin_move = picking.name
                            date_bl = datetime.strptime(picking.date.split(' ')[0], '%Y-%m-%d').strftime('%d-%m-%Y')

                    if pick_date and pick_date > date_borne:
                        continue

            if item.date:
                date_move = datetime.strptime(item.date.split(' ')[0], '%Y-%m-%d').strftime('%d-%m-%Y')

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

            line = invoice_line_env.create({'date_move': date_move,
                                            'origin': 'internal',
                                            'num_bl': origin_move,
                                            'date_bl':date_bl,
                                            'serial': serial,
                                            'create_date': date.today(),
                                            'price_unit': price_unit,
                                            'partner_id': partner_id,
                                            'company_id': company_id,
                                            'account_id': account_id.id,
                                            'uom_id': item.product_uom.id,
                                            'name': name,
                                            'product_id': item.product_id.id,
                                            'invoice_id': invoice.id,
                                            'quantity': item.product_qty,
                                            'move_id': item.id,
                                            })
            line._set_taxes()
            line.update({'price_unit': price_unit})
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
                                            'num_bl': item.get('origin', ''),
                                            'date_move': item.get('date', ''),
                                            'create_date': date.today(),
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
            if 'OR' in move.origin:
                if move.partner_id.company_id.id == 3:
                    list_ber.append(move)
                elif move.partner_id.company_id.id == 1:
                    list_atom.append(move)
            else:
                if move.partner_id.id == 6:
                    list_ber.append(move)

                elif move.partner_id.id == 1:
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
                                             'name': (line.user_id.name + " : " + line.name),
                                             'origin': repair.name,
                                             'date': line.date,
                                             'timesheet_id': line.id,
                                             })

                        if line.user_id.company_id.id == 3:
                            product_time = prod_env.search([('default_code', '=', 'TAMOEX')])

                            time_atom.append({'quantity': line.unit_amount,
                                              'product': product_time,
                                              'name': (line.user_id.name + " : " + line.name),
                                              'origin': repair.name,
                                              'date': line.date,
                                              'timesheet_id': line.id,
                                              })
                    else:

                        if line.user_id.company_id.id == 1:
                            product_time = prod_env.search([('default_code', '=', 'TBMO')])

                            time_ber.append({'quantity': line.unit_amount,
                                             'product': product_time,
                                             'name': (line.user_id.name + " : " + line.name),
                                             'origin': repair.name,
                                             'date': line.date,
                                             'timesheet_id': line.id,
                                             })

                        if line.user_id.company_id.id == 3:
                            product_time = prod_env.search([('default_code', '=', 'TAMO')])

                            time_atom.append({'quantity': line.unit_amount,
                                              'product': product_time,
                                              'name': (line.user_id.name + " : " + line.name),
                                              'origin': repair.name,
                                              'date': line.date,
                                              'timesheet_id': line.id,
                                              })
                else:

                    if line.user_id.company_id.id == 1:
                        product_time = prod_env.search([('default_code', '=', 'TBMO')])

                        time_ber.append({'quantity': line.unit_amount,
                                         'product': product_time,
                                         'name': (line.user_id.name + " : " + line.name),
                                         'date': line.date,
                                         'timesheet_id': line.id,
                                         })

                    if line.user_id.company_id.id == 3:
                        product_time = prod_env.search([('default_code', '=', 'TAMO')])

                        time_atom.append({'quantity': line.unit_amount,
                                          'product': product_time,
                                          'date': line.date,
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

        # On repartit les mouvements de ventes dans chaque list:
        list_ber, list_atom = self.get_move(moves)
        time_ber, time_atom = self.get_task(projet_line_task)


        ### CAS FACTURE VENTE BERAUD

        #Test si il y a une liste de bien echangee de ber -> atom
        if len(list_ber) !=0:
            account_id = partner_env.browse([6]).with_context(company_id=1).property_account_receivable_id.id
            journal_id_sale = journal_env.search([('company_id', '=', 1), ('type', '=', 'sale')])[0].id

            sale_invoice = self.create_invoice(6,1, 'out_invoice', account_id, journal_id_sale)
            sale_line_ids_goods = self.create_line_ids_for_goods(list_ber, 5, 6, 1, sale_invoice, 'out_invoice', journal_id_sale, date)
            sale_line_ids += sale_line_ids_goods

        # Test si il y a une liste de temps a facturer de ber -> atom
        if len(time_ber) != 0:
            if not sale_invoice:
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
                purchase_line_ids_goods = self.create_line_ids_for_goods(list_ber, 5, 1, 3, purchase_invoice, 'in_invoice', journal_id, date)
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
            sale_line_ids_goods = self.create_line_ids_for_goods(list_atom, 5, 1, 3, sale_invoice, 'out_invoice', journal_id_sale, date)
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
                purchase_line_ids_goods = self.create_line_ids_for_goods(list_atom, 5, 6, 1, purchase_invoice, 'in_invoice', journal_id, date)
                purchase_line_ids += purchase_line_ids_goods

            if len(time_atom) != 0:
                purchase_line_ids_timesheet = self.create_line_ids_for_timesheet(time_atom, 6, 1, purchase_invoice, 'in_invoice', journal_id)
                purchase_line_ids += purchase_line_ids_timesheet

            purchase_invoice.compute_taxes()


class inherit_AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    move_id = fields.Many2one("stock.move", help='link between the stock move and the invoice line')
    timesheet_id = fields.Many2one("account.analytic.line", help='link between the time on a project move and the invoice line')

    date_move = fields.Char('Date Mouvement')
    date_bl = fields.Char('Date BL/OR')


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

    @api.multi
    def action_cancel(self):
        res = super(inherit_AccountInvoice, self).action_cancel()

        for invoice in self:
            for invoice_line in invoice.invoice_line_ids:
                if invoice_line.move_id.id:
                    invoice_line.move_id.billed = False
                if invoice_line.timesheet_id.id:
                    invoice_line.timesheet_id.billed = False

        return res





class inherit_stock_move(models.Model):
    _inherit = 'stock.move'
    billed = fields.Boolean("Is billed", default=False, index=True)
    isSale = fields.Boolean(u"State move")


class inherit_analytic_line(models.Model):
    _inherit = 'account.analytic.line'
    billed = fields.Boolean("Is billed", default=False, index=True)
