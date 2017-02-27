# -*- coding: utf-8 -*-
from openerp import models, api, fields
from openerp.tools.translate import _
import csv
import datetime
import math
import base64
import StringIO
from openerp.exceptions import UserError

class Export_Journal(models.Model):
    _name = "export.ecriture_sage"

    #### Fields ####
    date_debut = fields.Date(string="Date debut")
    date_fin = fields.Date(string="Date fin")

    file_ber_vente = fields.Char(string='Filename', size=256, readonly=True)
    value_ber_vente = fields.Binary(readonly=True)

    file_ber_achat = fields.Char(string='Filename', size=256, readonly=True)
    value_ber_achat = fields.Binary(readonly=True)

    file_atm_vente = fields.Char(string='Filename', size=256, readonly=True)
    value_atm_vente = fields.Binary(readonly=True)

    file_atm_achat = fields.Char(string='Filename', size=256, readonly=True)
    value_atm_achat = fields.Binary(readonly=True)

    test = fields.Boolean('Test export', help=u"Si coché les lignes exportés ne seront pas marquées comme tel")

    def formatDate(self, dateEN):
        date = dateEN.split('-')
        formatted_date = date[2]+date[1]+date[0][-2:]
        return  formatted_date



    @api.multi
    def action_export(self, journal_id, value, date_debut, date_fin, filename, code, collectif, type, test):
        list_row = []

        account_move = self.env['account.move']
        account_move_env = self.env['account.move.line']
        data_move = account_move.search([('date', '>=', date_debut), ('date', '<=', date_fin), ('journal_id', '=', journal_id), ('exported', '=', False)])

        csvfile = StringIO.StringIO()
        fieldnames = ['Code journal', 'Date de piece', 'No de compte general', 'Intitule compte general', 'No de piece',
                      'No de facture', 'Reference', 'Reference rapprochement', 'No compte tiers', 'Code taxe', 'Provenance',
                      'Libelle ecriture', 'Mode de reglement', 'Date d echeance', 'Code ISO devise',
                      'Montant de la devise', 'Type de norme', 'Sens', 'Montant', 'Montant signe','Montant debit',
                      'Montant credit', 'Type d ecriture','No de plan analytique', 'No de section', 'Information libre 1']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        for move in data_move:
            data__line = account_move_env.search([('move_id', '=', move.id)], order='id desc')
            dict_sum_line = {}
            tax = [x.tax_line_id.description for x in data__line if x.tax_line_id]

            for line in data__line:
                print 'move_line_id: ', line.id
                montant = str(math.fabs(line.amount_residual))
                sens = ""
                note = ""
                origine = ""
                dateL = ""
                tier = ""
                nbcompte = ""
                nomcompte = ""
                nb_piece = ""
                nb_invoice = ""
                label = ""
                date_due = ""
                term = ""
                compte = ""
                tax_code = ""

                if line.invoice_id.origin:
                    origine = line.invoice_id.origin[:17].encode("windows-1252")
                if line.invoice_id.reference :
                    origine = line.invoice_id.origin[:17].encode("windows-1252")
                if line.internal_note:
                    note = line.internal_note.encode("windows-1252")
                if line.debit == 0:
                    sens = "C"
                else:
                    sens = "D"
                if line.date:
                    dateL = self.formatDate(line.date)
                if line.account_id.code:
                    nbcompte = line.account_id.code[:8]
                    if 'CA' in nbcompte or 'CB' in nbcompte or 'F' in nbcompte:
                        compte = collectif

                        if line.partner_id:
                            if type == "vente":
                                tier = line.partner_id.property_account_receivable_id.code[:20]
                            if type == "achat":
                                tier = line.partner_id.property_account_payable_id.code[:20]

                    else:
                        compte = nbcompte
                    if compte == '445201':
                        compte = '44520000'
                    if len(compte) < 8:
                        raise UserError(_("Il semblerait que la facture ID : %s n'utilise pas un compte comptable (%s) valide dans Sage : [Code err: 03]]" % (line.invoice_id.id, compte)))

                if line.account_id.name:
                    nomcompte = line.account_id.name[:40].encode("windows-1252")
                if line.invoice_id.number:
                    nb_piece = str(line.invoice_id.number)[:13]
                if line.invoice_id.number:
                    nb_invoice = str(line.invoice_id.number)[:10]

                if line.invoice_id:
                    label_type = "Facture "
                    if 'refund' in line.invoice_id.type:
                        label_type = "Avoir "

                    if line.invoice_id.partner_id.name:
                        label = label_type + line.invoice_id.partner_id.name.encode("windows-1252")
                    elif line.invoice_id.partner_id.display_name:
                        label = label_type + line.invoice_id.partner_id.display_name.encode("windows-1252")
                    else:
                        raise UserError(_("Une erreur c'est produite lors de l'export veuillez contacter votre administrateur : [Code err : 01]"))


                if line.invoice_id.date_due:
                    date_due = self.formatDate(line.invoice_id.date_due)

                if compte[0] not in ['7', '6']:
                    tax_code = ""
                elif 'ACEE' in tax:
                    tax_code = 'ACEE'
                else:
                    if tax:
                        tax_code = tax[0]

                if line.invoice_id.payment_term_id:
                    if line.invoice_id.payment_term_id.type_sage :
                        term = line.invoice_id.payment_term_id.type_sage
                    else :
                        raise UserError(_("Il semblerait que la facture ID : %s n'utilise pas une condition de paiement valide dans Sage : [Code err: 02]]" %(line.invoice_id.id)))

                if not compte in dict_sum_line:
                    dict_sum_line[compte] = {'Code journal': code,
                                             'Date de piece': dateL,
                                             'No de compte general': compte,
                                             'Intitule compte general': nomcompte,
                                             'No de piece': nb_piece,
                                             'No de facture': nb_invoice,
                                             'Reference': origine,
                                             'Reference rapprochement': "",
                                             'No compte tiers': tier,
                                             'Code taxe': tax_code.encode("windows-1252"),
                                             'Provenance': "A",
                                             'Libelle ecriture': label,
                                             'Mode de reglement': term.encode("windows-1252"),
                                             'Date d echeance': date_due,
                                             'Code ISO devise': "",
                                             'Montant de la devise': "",
                                             'Type de norme': "D",
                                             'Sens': sens,
                                             'Montant': montant[:12],
                                             'Montant signe': str(line.amount_residual).replace('.', ',')[:13].encode("windows-1252") ,
                                             'Montant debit': str(line.debit).replace('.', ',')[:12].encode("windows-1252") ,
                                             'Montant credit': str(line.credit).replace('.', ',')[:12].encode("windows-1252"),
                                             'Type d ecriture':"G",
                                             'No de plan analytique':"0",
                                             'No de section':"",
                                             'Information libre 1': note,
                                             }
                else :
                    dict_sum_line[nbcompte]['Montant'] = str(float(dict_sum_line[nbcompte]['Montant'].replace(',', '.')) + float(montant))[:12]
                    dict_sum_line[nbcompte]['Montant signe'] = str(float(dict_sum_line[nbcompte]['Montant signe'].replace(',', '.')) + line.amount_residual)[:13]
                    dict_sum_line[nbcompte]['Montant debit'] = str(float(dict_sum_line[nbcompte]['Montant debit'].replace(',', '.')) + line.debit)[:12]
                    dict_sum_line[nbcompte]['Montant credit'] = str(float(dict_sum_line[nbcompte]['Montant credit'].replace(',', '.')) + line.credit)[:12]
            print sorted(dict_sum_line, reverse=True)
            for dict in sorted(dict_sum_line, reverse=True):
                print dict
                dict_sum_line[dict]['Montant'] = "{0:.2f}".format(float(dict_sum_line[dict]['Montant']))

                if '-' in dict_sum_line[dict]['Montant signe']:
                    dict_sum_line[dict]['Montant signe'] = ('-' + "{0:.2f}".format(float(dict_sum_line[dict]['Montant signe'].strip("-").replace(',', '.')))).replace(',', '.')
                else:
                    dict_sum_line[dict]['Montant signe'] = ("{0:.2f}".format(float(dict_sum_line[dict]['Montant signe'].replace(',', '.')))).replace('.', ',')

                dict_sum_line[dict]['Montant debit'] = "{0:.2f}".format(float(dict_sum_line[dict]['Montant debit'].replace(',', '.'))).replace('.', ',')
                dict_sum_line[dict]['Montant credit'] = "{0:.2f}".format(float(dict_sum_line[dict]['Montant credit'].replace(',', '.'))).replace('.', ',')
                list_row.append(dict_sum_line[dict])

            if not test:
                move.exported = True
        writer.writerows(list_row)
        fecvalue = csvfile.getvalue()
        self.write({
            value: base64.encodestring(fecvalue),
            filename: filename,
        })
        csvfile.close()


    @api.multi
    def action_ber_vente(self):
        journal_env = self.env['account.journal']

        date = str(datetime.date.today())
        journal_id = journal_env.search([('type', '=', 'sale'), ('company_id', '=', 1)]).id
        self.write({'file_ber_vente': "Export Beraud Vente %s" % (date)})

        value = 'value_ber_vente'
        filename = 'file_ber_vente'
        name = "Export Beraud Vente %s" %date
        nb_compte_collectif = '41100000'
        test = self.test

        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename, 'V1', nb_compte_collectif, 'vente', test)

        action = {
            'name': 'ecriture_sage',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action

    @api.multi
    def action_ber_achat(self):
        journal_env = self.env['account.journal']

        date = str(datetime.date.today())
        journal_id = journal_env.search([('type', '=', 'purchase'), ('company_id', '=', 1)]).id
        self.write({'file_ber_achat': "Export Beraud Achat %s" % (date)})

        value = 'value_ber_achat'
        filename = 'file_ber_achat'
        name = "Export Beraud Achat %s" % date
        nb_compte_collectif = '40100000'
        test = self.test

        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename, 'A1', nb_compte_collectif, 'achat', test)

        action = {
            'name': 'ecriture_sage',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action

    @api.multi
    def action_atm_vente(self):
        journal_env = self.env['account.journal']

        date = str(datetime.date.today())
        journal_id = journal_env.search([('type', '=', 'sale'), ('company_id', '=', 3)]).id
        self.write({'file_atm_vente': "Export Atom Vente %s" % (date)})

        value = 'value_atm_vente'
        filename = 'file_atm_vente'
        name = "Export Atom Vente %s" % date
        nb_compte_collectif = '41100000'
        test = self.test


        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename, 'V1', nb_compte_collectif, 'vente', test)

        action = {
            'name': 'ecriture_sage',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action

    @api.multi
    def action_atm_achat(self):
        journal_env = self.env['account.journal']

        date = str(datetime.date.today())
        journal_id = journal_env.search([('type', '=', 'purchase'), ('company_id', '=', 3)]).id
        self.write({'file_atm_achat': "Export Atom Achat %s" % (date)})

        value = 'value_atm_achat'
        filename = 'file_atm_achat'
        name = "Export Atom Achat %s" % date
        nb_compte_collectif = '40100000'
        test = self.test

        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename, 'A1', nb_compte_collectif, 'achat', test)

        action = {
            'name': 'ecriture_sage',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action


class AccountMove(models.Model):
    _inherit = 'account.move'

    exported = fields.Boolean()


class Export_Tiers(models.Model):
    _name = 'export.tier'

    file_client_ber = fields.Char(string='Filename', size=256, readonly=True)
    value_client_ber = fields.Binary(readonly=True)

    file_client_atm = fields.Char(string='Filename', size=256, readonly=True)
    value_client_atm = fields.Binary(readonly=True)

    @api.multi
    def action_export(self, company_id, value, filename):

        list_row = []
        partner_env = self.env['res.partner']
        sale_env = self.env['sale.order']
        purchase_env = self.env['purchase.order']
        invoice_env = self.env['account.invoice']

        csvfile = StringIO.StringIO()
        fieldnames = [u'Numero compte', u'intitule', 'Type', u'N compte principal', u'Qualite',
                    'Classement', 'Contact', 'Adresse', u'Complement adresse', 'Code postal', 'Ville',
                    u'Region', 'Pays', u'Telephone', u'Telecopie', 'Adresse Email', 'Site', 'NAF (APE)',
                    u'N Identifiant', u'N Siret', u'Intitule banque', 'Structure banque', 'Code banque',
                    'Guichet banque', 'Compte banque', u'Cle banque', 'Code ISO devise banque',
                    'Adresse banque', 'Code postal banque', 'Ville banque', 'Pays banque',
                    'Code BIC banque', 'Code IBAN banque', 'Information libre 1']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        partners = partner_env.search([('exported', '=', False), ('company_id', '=', company_id)])

        for partner in partners:
            contact = ""
            ref = ""
            code = ""
            street = ""
            street2 = ""
            zip = ""
            city = ""
            country_id = ""
            phone = ""
            fax = ""
            email = ""
            comment = ""

            if partner.company_type == "company":
                partner_fils = partner_env.search([('type', '=', 'invoice'), ('parent_id', '=', partner.id), ('is_principal', '=', True)], limit=1)

                sale = sale_env.search([('partner_id', '=', partner.id), ('state', 'in', ['sale', 'done'])])
                purchase = purchase_env.search([('partner_id', '=', partner.id), ('state', 'in', ['purchase', 'done'])])
                invoice = invoice_env.search([('partner_id', '=', partner.id), ('state', 'in', ['open', 'paid'])])

                if sale or purchase or invoice:
                    if partner_fils:
                        contact = partner_fils.title + " " + partner_fils.name
                        contact = contact[:35].encode("windows-1252")
                    if partner.customer:
                        if partner.ref:
                            ref = partner.ref.strip()[:17].encode("windows-1252")
                        if partner.property_account_receivable_id:
                            code = partner.property_account_receivable_id.code.encode("windows-1252")
                        if partner.street:
                            street2 = partner.street[:35].encode("windows-1252")
                        if partner.street2:
                            street = partner.street2[:35].encode("windows-1252")
                        if partner.zip:
                            zip = partner.zip[:9].encode("windows-1252")
                        if partner.city:
                            city = partner.city[:35].encode("windows-1252")
                        if partner.country_id:
                            country_id = partner.country_id.name[:35].encode("windows-1252")
                        if partner.phone:
                            phone = partner.phone[:21].encode("windows-1252")
                        if partner.fax:
                            fax = partner.fax[:21].encode("windows-1252")
                        if partner.email:
                            email = partner.email[:69].encode("windows-1252")
                        if partner.comment:
                            comment = partner.comment.encode("windows-1252")

                        list_row.append({'Numero compte': code,
                                         u'intitule': partner.name[:35].encode("windows-1252"),
                                         'Type': 0,
                                         u'N compte principal': '41100000',
                                         u'Qualite': "",
                                         'Classement': partner.name[:17].encode("windows-1252"),
                                         'Contact': contact,
                                         'Adresse': street,
                                         u'Complement adresse': street2,
                                         'Code postal': zip,
                                         'Ville': city,
                                         u'Region': "",
                                         'Pays': country_id,
                                         u'Telephone': phone,
                                         u'Telecopie': fax,
                                         'Adresse Email': email,
                                         'Site': "",
                                         'NAF (APE)': "",
                                         u'N Identifiant': "",
                                         u'N Siret': "",
                                         u'Intitule banque': "",
                                         'Structure banque': 0,
                                         'Code banque': "",
                                         'Guichet banque': "",
                                         'Compte banque': "",
                                         u'Cle banque': "",
                                         'Code ISO devise banque': "",
                                         'Adresse banque': "",
                                         'Code postal banque': "",
                                         'Ville banque': "",
                                         'Pays banque': "",
                                         'Code BIC banque': "",
                                         'Code IBAN banque': "",
                                         'Information libre 1': comment,
                                         })
                    if partner.supplier:
                        if partner.ref:
                            ref = partner.ref.strip()[:17].encode("windows-1252")
                        if partner.property_account_receivable_id:
                            code = partner.property_account_payable_id.code.encode("windows-1252")
                        if partner.street:
                            street2 = partner.street[:35].encode("windows-1252")
                        if partner.street2:
                            street = partner.street2[:35].encode("windows-1252")
                        if partner.zip:
                            zip = partner.zip[:9].encode("windows-1252")
                        if partner.city:
                            city = partner.city[:35].encode("windows-1252")
                        if partner.country_id:
                            country_id = partner.country_id.name[:35].encode("windows-1252")
                        if partner.phone:
                            phone = partner.phone[:21].encode("windows-1252")
                        if partner.fax:
                            fax = partner.fax[:21].encode("windows-1252")
                        if partner.email:
                            email = partner.email[:69].encode("windows-1252")
                        if partner.comment:
                            comment = partner.comment.encode("windows-1252")

                        list_row.append({'Numero compte':code,
                                         u'intitule': partner.name[:35].encode("windows-1252"),
                                         'Type': 1,
                                         u'N compte principal': '40100000',
                                         u'Qualite': "",
                                         'Classement': partner.name[:17].encode("windows-1252"),
                                         'Contact': contact,
                                         'Adresse': street,
                                         u'Complement adresse': street2,
                                         'Code postal': zip,
                                         'Ville': city,
                                         u'Region': "",
                                         'Pays': country_id,
                                         u'Telephone': phone,
                                         u'Telecopie': fax,
                                         'Adresse Email': email,
                                         'Site': "",
                                         'NAF (APE)': "",
                                         u'N Identifiant': "",
                                         u'N Siret': "",
                                         u'Intitule banque': "",
                                         'Structure banque': 0,
                                         'Code banque': "",
                                         'Guichet banque': "",
                                         'Compte banque': "",
                                         u'Cle banque': "",
                                         'Code ISO devise banque': "",
                                         'Adresse banque': "",
                                         'Code postal banque': "",
                                         'Ville banque': "",
                                         'Pays banque': "",
                                         'Code BIC banque': "",
                                         'Code IBAN banque': "",
                                         'Information libre 1': comment })
                    partner.write({'exported': True})
        writer.writerows(list_row)
        fecvalue = csvfile.getvalue()
        self.write({
            value: base64.encodestring(fecvalue),
            filename: filename,
        })
        csvfile.close()


    @api.multi
    def action_tier_ber(self):
        date = str(datetime.date.today())
        name = "Export Tier Beraud %s" % date
        company_id = 1
        value = 'value_client_ber'
        filename = 'file_client_ber'

        self.action_export(company_id, value, filename)

        action = {
            'name': 'export.tier',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=export.tier&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }
        return action

    @api.multi
    def action_tier_atm(self):
        date = str(datetime.date.today())
        name = "Export Tier Atom %s" % date
        company_id = 3
        value = 'value_client_atm'
        filename = 'file_client_atm'
        self.action_export(company_id, value, filename)

        action = {
            'name': 'export.tier',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=export.tier&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }
        return action


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    exported = fields.Boolean()

    @api.multi
    def write(self, vals):
        if not len(vals.keys()) == 1 and vals.keys()[0] == 'exported':
            vals['exported'] = False
        record_write = super(ResPartnerInherit, self).write(vals)
        return record_write

    @api.model
    def create(self, vals):
        vals['exported'] = False
        record = super(ResPartnerInherit, self).create(vals)
        return record
