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

fich_ = open('fournisseurs_ATOM.csv', 'rb')

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
MAP_COMPTES_VENTE = {'70711000' : 1334,
                     '70712000' : 1334,
                     '70721000' : 1335}

MAP_COMPTES_ACHAT = {'60711000' : 1152,
                     '60712000' : 1152,
                     '60711200' : 1152,
                     '60721000' : 1153}

MAP_UNITES = {'kg': 3,
              'cm': 10}

MAP_COMMERCIAUX = {'NDEB': 2,
                   'test': 3}

tot_cree = 0

for row in csvreader:
    if row[0] == "Feu": continue
    
    ref_interne = row[2]
    nom = row[3]
    zip_code = row[4]
    city = row[5]
    
    if row[6]:
        nom = row[6] + ' ' + nom
        
    addr_complement = row[7] + ' ' + row[8]
    street = row[9]
    localite = row[10]
    
    code_pays = row[11]
    
    if not code_pays: code_pays = 'FR'
    
    # recherche code pays
    country_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('code','=', code_pays)])
    
    telephone = row[12]
    fax = row[13]
    
    website = row[14]
    email = row[15]
    
    activite = row[17]
    geographique = row[18]
    mistral = row[19]
    

    conditions_reglement = row[39]
    devise = row[40]
    langue = row[41]
    
    code_naf = row[62]
    siret = row[63]
    
    compte = row[65]
    
    vat_number = row[70]
    
    if 'FR' in langue:
        langue = 'fr_FR'
    else:
        langue = 'en_US'
        
    partner_dict = {'ref' : ref_interne,
                    'name': nom,
                    'zip': zip_code,
                    'city': city,
                    'phone': telephone,
                    'fax': fax,
                    'website': website,
                    'country_id': country_id[0],
                    'lang': langue,
                    'vat': vat_number,
                    'company_id': 3, # Atom
                    'notify_email': 'none',
                    'company_type': 'company',
                    'customer': False,
                    'supplier': True,
                    #'user_id': MAP_COMMERCIAUX[commercial],
                    'email': email}

    print partner_dict

    try :
        partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'create', partner_dict)

    except :
        partner_dict['vat'] = ''
        partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'create', partner_dict)

    tot_cree += 1

print "Nombre clients crees : " + str(tot_cree)
