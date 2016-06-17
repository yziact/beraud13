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

fich_ = open('parc_machines.csv', 'rb')

csvreader = csv.reader(fich_, delimiter=';')


# ['R\xc3\xa9f\xc3\xa9rence', 'D\xc3\xa9signation', 'Remplac\xc3\xa9 par', 'Tenu en stock ?', 'Mode de suivi',
# 'G\xc3\xa9rer les r\xc3\xa9servations', 'Nature', 'Ss-r\xc3\xa9f\xc3\xa9rence', 'Fonction', 'Marque',
# 'Type \xc3\xa9quipement LUCI', 'Poids brut', 'Poids net', 'Unit\xc3\xa9 poids', ' Dimension 1 ', ' Dimension 2 ', ' Dimension 3 ',
# 'Unit\xc3\xa9 dimension', 'Fournisseur', 'Marge mini', 'Quantit\xc3\xa9 en stock', 'En commande fournisseur', 'R\xc3\xa9serv\xc3\xa9 client',
# 'En commande client', 'Dernier inventaire', 'Garantie', 'P\xc3\xa9remption', 'ABC', 'Compte vente', 'Compte achat', 'Compte stock',
# 'TVA vente', 'TVA achat', 'Nomenclature douane', 'R\xc3\xa9gime \xc3\xa9change DEB', 'Saisie pi\xc3\xa8ce client',
# 'Saisie pi\xc3\xa8ce fournisseur', 'Saisie pi\xc3\xa8ce interne', 'Derni\xc3\xa8re op\xc3\xa9ration le', 'Cr\xc3\xa9\xc3\xa9 par',
# 'Cr\xc3\xa9\xc3\xa9 le', 'Modifi\xc3\xa9 par', 'Modifi\xc3\xa9 le']


# Nom du compte : id
MAP_COMPTES_VENTE = {'70711000' : 624,
                     '70712000' : 624,
                     '70721000' : 625}

MAP_COMPTES_ACHAT = {'60711000' : 442,
                     '60712000' : 442,
                     '60721000' : 443}

MAP_UNITES = {'kg': 3,
              'cm': 10}

tot_cree = 0

for row in csvreader:
    if row[3] == "Tenu en stock ?": continue
    reference_interne = row[0]
    designation = row[1]

    # WTF 'extérieur' ?
    if row[3] == 'En stock':
        type_p = 'product'
    else:
        type_p = 'product'
    
    if 'Par no' in row[4]: 
        suivi_produit = 'serial'
    else:
        suivi_produit = 'none'
    
    unite_mesure = 'kg'
    
    unite_dimension = 'cm'
    
    poids = str_to_float(row[12])
    
    largeur = str_to_float(row[14])
    hauteur = str_to_float(row[15])
    longueur = str_to_float(row[16])
    
    garantie_mois = str_to_float(row[25])
    
    compte_vente = row[28]
    compte_achat = row[29]
    
    code_douane = row[33]
    
    
    product_template_dict = {'name': designation,
                    'default_code': reference_interne,
                    'type': type_p,
                    'tracking': suivi_produit,
                    'weight': poids,
                    'property_account_income_id': MAP_COMPTES_VENTE[compte_vente],
                    'property_account_expense_id': MAP_COMPTES_ACHAT[compte_achat],
                    'warranty': garantie_mois,
                    'uom_id': MAP_UNITES[unite_mesure],
                    'uom_po_id': MAP_UNITES[unite_mesure],
                    'code_douane': code_douane,
                    }
    
    product_template_id = sock.execute(dbname, uid, pwd, 'product.template', 'create', product_template_dict)
    
    product_dict = {'length' : longueur,
                    'width': largeur,
                    'height': hauteur}
    
    product_id = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('product_tmpl_id','=',product_template_id)])
    
    if product_id:
        sock.execute(dbname, uid, pwd, 'product.product', 'write', product_id, product_dict)
        
    tot_cree += 1


print "Nombre produits crees : " + str(tot_cree)
