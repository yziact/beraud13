# -*- coding: utf-8 -*-
from openerp import models, api, fields
import csv
import datetime
import math
import base64
import StringIO



class Export_Journal(models.Model):
    _name = "export.ecriture_sage"

#### Fields ####

    # ber_vente = fields.Boolean("Journal vente Beraud")
    # ber_achat = fields.Boolean("Journal achat Beraud")
    # atm_vente = fields.Boolean("Journal vente Atome ")
    # atm_achat = fields.Boolean("Journal vente Atome")
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


    @api.multi
    def action_export(self, journal_id, value, date_debut, date_fin, filename):
        list_row = []
        account_move_env = self.env['account.move.line']
        data__line = account_move_env.search([('date', '>=', date_debut), ('date', '<=', date_fin), ('journal_id', '=', journal_id)])

        csvfile = StringIO.StringIO()

        fieldnames = ['Code journal', 'Date de piece', 'No de compte general', 'Intitule compte general', 'No de piece',
                      'No de facture', 'Reference', 'Reference rapprochement', 'No compte tiers', 'Code taxe', 'Provenance',
                      'Libelle ecriture', 'Mode de reglement', 'Date d echeance', 'Code ISO devise',
                      'Montant de la devise', 'Type de norme', 'Sens', 'Montant', 'Montant signe','Montant debit',
                      'Montant credit', 'Type d ecriture','No de plan analytique', 'No de section', 'Information libre 1']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for line in data__line:
            montant = str(math.fabs(line.amount_residual))
            sens = ""
            note = ""
            origine = ""
            if line.invoice_id.origin:
                origine = line.invoice_id.origin.encode("utf-8")
            if line.internal_note:
                note = line.internal_note.encode("utf-8")
            if line.debit == 0:
                sens = "C"
            else:
                sens = "D"

            list_row.append({'Code journal': line.journal_id.code[:4].encode("utf-8"),
                             'Date de piece': line.date.encode("utf-8"),
                             'No de compte general': line.account_id.code[:8].encode("utf-8"),
                             'Intitule compte general': line.account_id.name[:40].encode("utf-8"),
                             'No de piece': str(line.invoice_id.number)[:13],
                             'No de facture': str(line.invoice_id.number)[:10],
                             'Reference': origine,
                             'Reference rapprochement':"",
                             'No compte tiers': line.partner_id.ref[:20].encode("utf-8"),
                             'Code taxe': "",#line.tax_line_id.tax_id.description,
                             'Provenance': "A",
                             'Libelle ecriture':line.account_id.name.encode("utf-8"),
                             'Mode de reglement': "",
                             'Date d echeance': "",
                             'Code ISO devise': "",
                             'Montant de la devise': "",
                             'Type de norme': "D",
                             'Sens': sens,
                             'Montant': montant[:12],
                             'Montant signe': str(line.amount_residual)[:13],
                             'Montant debit': str(line.debit)[:12],
                             'Montant credit': str(line.credit)[:12],
                             'Type d ecriture':"G",
                             'No de plan analytique':"",
                             'No de section':"",
                             'Information libre 1': note,
                             })

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

        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename)

        action = {
            'name': 'FEC',
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
        journal_id = journal_env.search([('type', 'is', 'purchase'), ('company_id', '=', 1)]).id
        self.write({'file_ber_achat': "Export Beraud Achat %s" % (date)})

        value = 'value_ber_achat'
        filename = 'file_ber_achat'
        name = "Export Beraud Achat %s" % date

        self.action_export(journal_id, value, self.date_debut, self.date_fin)

        action = {
            'name': 'FEC',
            'type': 'ir.actions.act_url',
            'code': '',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action

    @api.multi
    def action_atm_vente(self):
        journal_env = self.env['account.journal']

        date = str(datetime.date.today())
        journal_id = journal_env.search([('type', 'is', 'sale'), ('company_id', '=', 3)]).id
        self.write({'file_atm_vente': "Export Atom Vente %s" % (date)})

        value = 'value_atm_vente'
        filename = 'file_atm_vente'
        name = "Export Atom Vente %s" % date

        self.action_export(journal_id, value, self.date_debut, self.date_fin)

        action = {
            'name': 'FEC',
            'type': 'ir.actions.act_url',
            'code': '',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action

    @api.multi
    def action_atm_achat(self):
        journal_env = self.env['account.journal']

        date = str(datetime.date.today())
        journal_id = journal_env.search([('type', 'is', 'purchase'), ('company_id', '=', 3)]).id
        self.write({'file_atm_achat': "Export Atom Achat %s" % (date)})

        value = 'value_atm_achat'
        filename = 'file_atm_achat'
        name = "Export Atom Achat %s" % date

        self.action_export(journal_id, value, self.date_debut, self.date_fin)

        action = {
            'name': 'FEC',
            'type': 'ir.actions.act_url',
            'code': '',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action









# class Export_Tiers(models.Model):
#     _inherit = 'res.partner'
#
#     _PATH = "/tmp/"
#     _FILENAME = str(time.time()).replace('.', ',') + '.csv'
#
#     # TODO: modif export Tier
#     @api.multi
#     def write(self, vals):
#         record_write = super(Export_Tiers, self).write(vals)
#         partner_env = self.env['res.partner']
#         contact = ""
#
#         record = self.ensure_one()
#         if record.company_type == "company":
#
#             with open((self._PATH + self._FILENAME), 'wb') as csvfile:
#                 fieldnames = [u'Numero compte', u'intitule', 'Type', u'N compte principal', u'Qualite',
#                               'Classement', 'Contact', 'Adresse', u'Complement adresse', 'Code postal', 'Ville',
#                               u'Region', 'Pays', u'Telephone', u'Telecopie', 'Adresse Email', 'Site', 'NAF (APE)',
#                               u'N Identifiant', u'N Siret', u'Intitule banque', 'Structure banque', 'Code banque',
#                               'Guichet banque', 'Compte banque', u'Cle banque', 'Code ISO devise banque',
#                               'Adresse banque', 'Code postal banque', 'Ville banque', 'Pays banque',
#                               'Code BIC banque', 'Code IBAN banque', 'Information libre 1']
#                 writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
#                 writer.writeheader()
#
#                 partner_fils = partner_env.search([('type', '=', 'invoice'), ('parent_id', '=', record.id)],
#                                                   limit=1)
#
#                 if partner_fils:
#                     contact = partner_fils.title + " " + partner_fils.name
#
#                 if record.customer:
#                     writer.writerow({'Numero compte': record.ref.strip()[:17],
#                                      u'intitule': record.name[:35],
#                                      'Type': 0,
#                                      u'N compte principal': record.property_account_receivable_id.code,
#                                      u'Qualite': "",
#                                      'Classement': record.name[:17],
#                                      'Contact': contact[:35],
#                                      'Adresse': record.street[:35],
#                                      u'Complement adresse': record.street2[:35],
#                                      'Code postal': record.zip[:9],
#                                      'Ville': record.city[:35],
#                                      u'Region': "",
#                                      'Pays': record.country_id.name[:35],
#                                      u'Telephone': record.phone[:21],
#                                      u'Telecopie': record.fax[:21],
#                                      'Adresse Email': record.email[:69],
#                                      'Site': "",
#                                      'NAF (APE)': "",
#                                      u'N Identifiant': "",
#                                      u'N Siret': "",
#                                      u'Intitule banque': "",
#                                      'Structure banque': 0,
#                                      'Code banque': "",
#                                      'Guichet banque': "",
#                                      'Compte banque': "",
#                                      u'Cle banque': "",
#                                      'Code ISO devise banque': "",
#                                      'Adresse banque': "",
#                                      'Code postal banque': "",
#                                      'Ville banque': "",
#                                      'Pays banque': "",
#                                      'Code BIC banque': "",
#                                      'Code IBAN banque': "",
#                                      'Information libre 1': record.comment or ""
#                                      })
#
#                 if record.supplier:
#                     writer.writerow({'Numero compte': record.ref[:17],
#                                      u'intitule': record.name[:35],
#                                      'Type': 1,
#                                      u'N compte principal': record.property_account_payable_id.code,
#                                      u'Qualite': "",
#                                      'Classement': record.name[:17],
#                                      'Contact': contact[:35],
#                                      'Adresse': record.street[:35],
#                                      u'Complement adresse': record.street2[:35],
#                                      'Code postal': record.zip[:9],
#                                      'Ville': record.city[:35],
#                                      u'Region': "",
#                                      'Pays': record.country_id.name[:35],
#                                      u'Telephone': record.phone[:21],
#                                      u'Telecopie': record.fax[:21],
#                                      'Adresse Email': record.email[:69],
#                                      'Site': "",
#                                      'NAF (APE)': "",
#                                      u'N Identifiant': "",
#                                      u'N Siret': "",
#                                      u'Intitule banque': "",
#                                      'Structure banque': 0,
#                                      'Code banque': "",
#                                      'Guichet banque': "",
#                                      'Compte banque': "",
#                                      u'Cle banque': "",
#                                      'Code ISO devise banque': "",
#                                      'Adresse banque': "",
#                                      'Code postal banque': "",
#                                      'Ville banque': "",
#                                      'Pays banque': "",
#                                      'Code BIC banque': "",
#                                      'Code IBAN banque': "",
#                                      'Information libre 1': record.comment or ""
#                                      })
#
#             csvfile.close()
#         return record_write
#
#     @api.model
#     def create(self, vals):
#         record = super(Export_Tiers, self).create(vals)
#         partner_env = self.env['res.partner']
#         contact = ""
#
#         if record.company_type == "company":
#             with open((self._PATH + self._FILENAME), 'wb') as csvfile:
#                 fieldnames = [u'Numero compte', u'intitule', 'Type', u'N compte principal', u'Qualite',
#                               'Classement',
#                               'Contact', 'Adresse', u'Complement adresse', 'Code postal', 'Ville', u'Region',
#                               'Pays',
#                               u'Telephone', u'Telecopie', 'Adresse Email', 'Site', 'NAF (APE)', u'N Identifiant',
#                               u'N Siret', u'Intitule banque', 'Structure banque', 'Code banque', 'Guichet banque',
#                               'Compte banque', u'Cle banque', 'Code ISO devise banque', 'Adresse banque',
#                               'Code postal banque', 'Ville banque', 'Pays banque', 'Code BIC banque',
#                               'Code IBAN banque', 'Information libre 1']
#                 writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
#                 writer.writeheader()
#
#                 partner_fils = partner_env.search([('type', '=', 'invoice'), ('parent_id', '=', record.id)],
#                                                   limit=1)
#
#                 if partner_fils:
#                     contact = partner_fils.title + " " + partner_fils.name
#
#                 if record.customer:
#                     writer.writerow({'Numero compte': record.ref[:17],
#                                      u'intitule': record.name[:35],
#                                      'Type': 0,
#                                      u'N compte principal': record.property_account_receivable_id.code,
#                                      u'Qualite': "",
#                                      'Classement': record.name[:17],
#                                      'Contact': contact[:35],
#                                      'Adresse': record.street[:35],
#                                      u'Complement adresse': record.street2[:35],
#                                      'Code postal': record.zip[:9],
#                                      'Ville': record.city[:35],
#                                      u'Region': "",
#                                      'Pays': record.country_id.name[:35],
#                                      u'Telephone': record.phone[:21],
#                                      u'Telecopie': record.fax[:21],
#                                      'Adresse Email': record.email[:69],
#                                      'Site': "",
#                                      'NAF (APE)': "",
#                                      u'N Identifiant': "",
#                                      u'N Siret': "",
#                                      u'Intitule banque': "",
#                                      'Structure banque': 0,
#                                      'Code banque': "",
#                                      'Guichet banque': "",
#                                      'Compte banque': "",
#                                      u'Cle banque': "",
#                                      'Code ISO devise banque': "",
#                                      'Adresse banque': "",
#                                      'Code postal banque': "",
#                                      'Ville banque': "",
#                                      'Pays banque': "",
#                                      'Code BIC banque': "",
#                                      'Code IBAN banque': "",
#                                      'Information libre 1': record.comment or ""
#                                      })
#
#                 if record.supplier:
#                     writer.writerow({'Numero compte': record.ref[:17],
#                                      u'intitule': record.name[:35],
#                                      'Type': 1,
#                                      u'N compte principal': record.property_account_payable_id.code,
#                                      u'Qualite': "",
#                                      'Classement': record.name[:17],
#                                      'Contact': contact[:35],
#                                      'Adresse': record.street[:35],
#                                      u'Complement adresse': record.street2[:35],
#                                      'Code postal': record.zip[:9],
#                                      'Ville': record.city[:35],
#                                      u'Region': "",
#                                      'Pays': record.country_id.name[:35],
#                                      u'Telephone': record.phone[:21],
#                                      u'Telecopie': record.fax[:21],
#                                      'Adresse Email': record.email[:69],
#                                      'Site': "",
#                                      'NAF (APE)': "",
#                                      u'N Identifiant': "",
#                                      u'N Siret': "",
#                                      u'Intitule banque': "",
#                                      'Structure banque': 0,
#                                      'Code banque': "",
#                                      'Guichet banque': "",
#                                      'Compte banque': "",
#                                      u'Cle banque': "",
#                                      'Code ISO devise banque': "",
#                                      'Adresse banque': "",
#                                      'Code postal banque': "",
#                                      'Ville banque': "",
#                                      'Pays banque': "",
#                                      'Code BIC banque': "",
#                                      'Code IBAN banque': "",
#                                      'Information libre 1': record.comment or ""
#                                      })
#
#             csvfile.close()
#         return record
#
#

