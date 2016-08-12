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
            code = ""
            dateL = ""
            tier = ""
            nbcompte = ""
            nomcompte = ""
            nb_piece = ""
            nb_invoice = ""
            label = ""
            if line.invoice_id.origin:
                origine = line.invoice_id.origin.encode("utf-8")
            if line.internal_note:
                note = line.internal_note.encode("utf-8")
            if line.debit == 0:
                sens = "C"
            else:
                sens = "D"
            if line.journal_id.code:
                code = line.journal_id.code[:4].encode("utf-8")
            if line.date:
                dateL = line.date.encode("utf-8")
            if line.account_id.code:
                nbcompte = line.account_id.code[:8].encode("utf-8")
            if line.account_id.name:
                nomcompte = line.account_id.name[:40].encode("utf-8")
            if line.invoice_id.number :
                nb_piece = str(line.invoice_id.number)[:13]
            if line.invoice_id.number:
                nb_invoice = str(line.invoice_id.number)[:10]
            if line.partner_id.ref:
                tier = line.partner_id.ref[:20].encode("utf-8")
            if line.account_id.name :
                label = line.account_id.name.encode("utf-8")

            list_row.append({'Code journal': code,
                             'Date de piece': dateL ,
                             'No de compte general': nbcompte,
                             'Intitule compte general': nomcompte,
                             'No de piece': nb_piece,
                             'No de facture': nb_invoice ,
                             'Reference': origine,
                             'Reference rapprochement': "",
                             'No compte tiers': tier,
                             'Code taxe': "",
                             'Provenance': "A",
                             'Libelle ecriture': label,
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

        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename)

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

        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename)

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

        self.action_export(journal_id, value, self.date_debut, self.date_fin, filename)

        action = {
            'name': 'ecriture_sage',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=export.ecriture_sage&id=" + str(
                self.id) + "&filename_field=%s&field=%s&download=true&filename=%s.csv" % (filename, value, name),
            'target': 'new',
        }

        return action

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

                if partner_fils:
                    contact = partner_fils.title + " " + partner_fils.name
                    contact = contact[:35].encode("utf-8")
                if partner.customer:
                    if partner.ref:
                        ref = partner.ref.strip()[:17].encode("utf-8")
                    if partner.property_account_receivable_id:
                        code = partner.property_account_receivable_id.code.encode("utf-8")
                    if partner.street:
                        street = partner.street[:35].encode("utf-8")
                    if partner.street2:
                        street2 = partner.street2[:35].encode("utf-8")
                    if partner.zip:
                        zip = partner.zip[:9].encode("utf-8")
                    if partner.city:
                        city = partner.city[:35].encode("utf-8")
                    if partner.country_id:
                        country_id = partner.country_id.name[:35].encode("utf-8")
                    if partner.phone:
                        phone = partner.phone[:21].encode("utf-8")
                    if partner.fax:
                        fax = partner.fax[:21].encode("utf-8")
                    if partner.email:
                        email = partner.email[:69].encode("utf-8")
                    if partner.comment:
                        comment = partner.comment.encode("utf-8")

                    list_row.append({'Numero compte': ref,
                                     u'intitule': partner.name[:35].encode("utf-8"),
                                     'Type': 0,
                                     u'N compte principal': code,
                                     u'Qualite': "",
                                     'Classement': partner.name[:17].encode("utf-8"),
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
                        ref = partner.ref.strip()[:17].encode("utf-8")
                    if partner.property_account_receivable_id:
                        code = partner.property_account_receivable_id.code.encode("utf-8")
                    if partner.street:
                        street = partner.street[:35].encode("utf-8")
                    if partner.street2:
                        street2 = partner.street2[:35].encode("utf-8")
                    if partner.zip:
                        zip = partner.zip[:9].encode("utf-8")
                    if partner.city:
                        city = partner.city[:35].encode("utf-8")
                    if partner.country_id:
                        country_id = partner.country_id.name[:35].encode("utf-8")
                    if partner.phone:
                        phone = partner.phone[:21].encode("utf-8")
                    if partner.fax:
                        fax = partner.fax[:21].encode("utf-8")
                    if partner.email:
                        email = partner.email[:69].encode("utf-8")
                    if partner.comment:
                        comment = partner.comment.encode("utf-8")

                    list_row.append({'Numero compte':ref,
                                     u'intitule': partner.name[:35].encode("utf-8"),
                                     'Type': 1,
                                     u'N compte principal': code,
                                     u'Qualite': "",
                                     'Classement': partner.name[:17].encode("utf-8"),
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
                                     'Information libre 1': partner.comment })

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
        vals['exported'] = False
        record_write = super(ResPartnerInherit, self).write(vals)
        return record_write

    @api.multi
    def create(self, vals):
        vals['exported'] = False
        record = super(ResPartnerInherit, self).create(vals)
        return record
