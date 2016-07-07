#!/usr/bin/python
# -*- coding: utf-8 -*-

import xmlrpclib
import csv
import sys 
reload(sys) 
sys.setdefaultencoding("utf-8")
import unicodedata

def str_to_float(data):
    if data :
        for c in data:
            if ord(c) > 120: data = data.replace(c, '')
        try:
            return float(data.replace('-','').replace(',','.').replace('  ','').replace(' ',''))
        except:
            print "[*] Erreur"
            print data
            return ''
    else:
        return ''
    
username = "admin"
pwd = "X200yziact"
dbname = "BERAUD"

# Connexion Odoo
sock_common = xmlrpclib.ServerProxy("http://192.168.100.236:8069/xmlrpc/common")
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy("http://192.168.100.236:8069/xmlrpc/object")

# Variables 'en dur'
BERAUD_COMPANY_ID = 1
EUR_CURRENCY_ID = 1
PRODUCT_TYPE = 'product'

#
pricelist_id = False
supplier_id = False

fich_ = open('pieces_detachees.csv', 'rb')

csvreader = csv.reader(fich_, delimiter=';')

tot_cree = 0

for row in csvreader:
    print "[*] Produit " + str(tot_cree) + " :: " + str(row[5])
    if row[3] == "Article valide ?": continue
    reference = row[4]
    designation = row[5]
    prix_de_vente_1 = row[52]
    supplier = row[31]
    warranty = row[38]
    intrastat = row[44]
    compte_vente = row[39]
    compte_achat = row[40]
    prix_standard_beraud = str_to_float(row[52])
    prix_achat_atom = str_to_float(row[55])
    tva_vente_id = 1
    tva_achat_id = 6

    uom = row[14]
    if uom == 'KG':
        uom_id = 3
    else:
        uom_id = 1

    tracking = row[8]
    if tracking == 'Par no serie':
        tracking = 'serial'
    elif tracking == 'Par no lot':
        tracking = 'lot'
    else :
        tracking = 'none'

    uom_po = row[15]
    if uom_po == 'KG':
        uom_po_id = 3
    else:
        uom_po_id = 1

    if tot_cree == 0:
        # Creation de la pricelist au premier element
        pricelist_dict = {'name': 'prix Beraud pour Atom',
                          'company_id': BERAUD_COMPANY_ID,
                          'currency_id': EUR_CURRENCY_ID,
                          'active_list': True}

        pricelist_id = sock.execute(dbname, uid, pwd, 'product.pricelist', 'create', pricelist_dict)

    # Check des journaux comptables
    journal_achat_id = sock.execute(dbname, uid, pwd, 'account.account', 'search', [('code', '=', compte_achat), ('company_id', '=', BERAUD_COMPANY_ID)])
    if not journal_achat_id :
        journal_achat_dict = {'code': compte_achat,
                              'name': compte_achat,
                              'reconcile': True,
                              'company_id': BERAUD_COMPANY_ID,
                              'user_type_id': 2 } # Type == Payable
                              #'user_type_id': [(6, 0, 2)] } # Type == Payable
        journal_achat_id = sock.execute(dbname, uid, pwd, 'account.account', 'create', journal_achat_dict)
        journal_achat_id = [journal_achat_id]

    journal_vente_id = sock.execute(dbname, uid, pwd, 'account.account', 'search', [('code', '=', compte_vente), ('company_id', '=', BERAUD_COMPANY_ID)])
    
    if not journal_vente_id :
        journal_vente_dict = {'code': compte_vente,
                              'name': compte_vente,
                              'reconcile': True,
                              'company_id': BERAUD_COMPANY_ID,
                              'user_type_id': 1 } # Type == Payable
        journal_vente_id = sock.execute(dbname, uid, pwd, 'account.account', 'create', journal_vente_dict)
        journal_vente_id = [journal_vente_id]

    # Creation du product template
    product_template_dict = {'name': designation,
                    'default_code': reference,
                    'type': PRODUCT_TYPE,
                    'tracking': tracking,
                    'warranty': warranty,
                    'uom_id': uom_id,
                    'uom_po_id': uom_po_id,
                    'code_douane': intrastat,
                    'company_id': BERAUD_COMPANY_ID,
                    'purchase_method': 'receive',
                    'invoice_policy': 'delivery',
                    'taxes_id': [(6, 0, [1])], # Taxe 20 vente Beraud
                    'supplier_taxes_id': [(6, 0, [6])], # Taxe 20 achats Beraud
                    'property_account_income_id': journal_achat_id[0],
                    'property_account_expense_id': journal_vente_id[0],
    }

    if uom_id != uom_po_id:
        print "[*] UoM differents"
        product_template_dict['uom_po_id'] = uom_id
    
    product_template_id = sock.execute(dbname, uid, pwd, 'product.template', 'create', product_template_dict)

    product_dict = {'taxes_id': 1, # Taxe 20 vente Beraud
                    'supplier_taxes_id': 6, # Taxe 20 achats Beraud
                    'company_id': BERAUD_COMPANY_ID,
                    'property_account_income_id': journal_achat_id,
                    'property_account_expense_id': journal_vente_id }
    
    product_id = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('product_tmpl_id','=',product_template_id)])

    # Creation du prix fournisseur
    if supplier:
        supplier_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', supplier), ('company_id', '=', BERAUD_COMPANY_ID)])

        if supplier_id:
            supplier_dict = {'name': supplier_id[0],
                             'delay': 1,
                             'min_qty': 1,
                             'price': 0,
                             'product_tmpl_id': product_template_id,
                             'company_id': BERAUD_COMPANY_ID}

            supplier_line_id = sock.execute(dbname, uid, pwd, 'product.supplierinfo', 'create', supplier_dict)

    
    # Creation de l'item de la pricelist
    pricelist_item_dict = {'fixed_price': prix_achat_atom,
                           'sequence': 5,
                           'currency_id': EUR_CURRENCY_ID,
                           'applied_on': '1_product',
                           'company_id': BERAUD_COMPANY_ID,
                           'product_tmpl_id': product_template_id,
                           'pricelist_id': pricelist_id,
                           'base': 'list_price',
                           'compute_price': 'fixed',
                           'product_id': product_id[0] }

    pricelist_item_id = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'create', pricelist_item_dict)
    
    tot_cree += 1

print "Nombre produits crees : " + str(tot_cree)
