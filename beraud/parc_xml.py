import xmlrpclib
import csv
import sys
from datetime import datetime

reload(sys)
sys.setdefaultencoding("utf-8")

username = "admin"
pwd = "X200yziact"
dbname = "FACT_IS_TEST"

# Connexion Odoo
sock_common = xmlrpclib.ServerProxy("http://beraud.yziact.fr/xmlrpc/common")
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy("http://beraud.yziact.fr/xmlrpc/object")

fich_ = open('parcBERAUD.csv', 'rb')

csvreader = csv.reader(fich_, delimiter=';')

tot = 0
i = 1

row_tier = []
row_serial = []
row_machine = []
row_machine_mult = []
row_machine_ok = []

for row in csvreader:
    machine_id = ""

    if row[0] == 'Tiers':
        i += 1
        continue

    tiers = row[0]
    nom_tiers = row[1]
    type = row[2]
    nom_machine = row[3]
    marque = row[4]
    serial_num = row[5]
    qty = 1
    date_prod = False
    fin_garantie = False
    if row[6]:
        date_prod = row[6]
    if row[7]:
        fin_garantie = row[7]

    tier = sock.execute(dbname, uid, pwd, 'res.partner', 'search_read', [('ref', '=', tiers)])
    if not tier:
        i += 1
        # row_tier.append(i)
        continue

    machine = sock.execute(dbname, uid, pwd, 'product.product', 'search_read',
                           [('default_code', '=', type), ('name', 'ilike', nom_machine)],
                           ['id', 'name', 'default_code'])
    if not machine:
        i += 1
        # row_machine.append(i)
        continue
    elif len(machine) > 1:
        i += 1
        # row_machine_mult.append(i)
        continue
    else:
        # row_machine_ok.append(i)
        machine_id = machine[0]["id"]

        serial = sock.execute(dbname, uid, pwd, 'stock.production.lot', 'search_read', [('name', '=', serial_num)])
        if not serial:
            # row_serial.append(i)
            serial_id = sock.execute(dbname, uid, pwd, 'stock.production.lot', 'create',
                                     {'name': serial_num, 'product_id': machine_id})
            parc_machine_id = sock.execute(dbname, uid, pwd, 'parc_machine', 'create', {
                'product_id': machine_id,
                'lot_id': serial_id,
                'partner_id': tier[0]['id'],
                'location_id': 9,
                'company_id': 1,
                'date_prod': date_prod,

            })
            tot += 1

            row_machine_ok.append(i)
        else:
            parc_machine = sock.execute(dbname, uid, pwd, 'parc_machine', 'search_read',
                                        [('lot_id', '=', serial[0]['id'])])
            if not parc_machine:
                parc_machine_id = sock.execute(dbname, uid, pwd, 'parc_machine', 'create', {
                    'product_id': machine_id,
                    'lot_id': serial[0]['id'],
                    'partner_id': tier[0]['id'],
                    'location_id': 9,
                    'company_id': 1,
                    'date_prod': date_prod,
                    'date_guaranttee': fin_garantie,
                })
                tot += 1

                row_machine_ok.append(i)

            else:
                parc_machine = sock.execute(dbname, uid, pwd, 'parc_machine', 'search_read',
                                            [('lot_id', '=', serial[0]['id'])])
                if not parc_machine:
                    if not fin_garantie:
                        parc_machine_id = sock.execute(dbname, uid, pwd, 'parc_machine', 'create', {
                            'product_id': machine_id,
                            'lot_id': serial[0]['id'],
                            'partner_id': tier[0]['id'],
                            'location_partner': tier[0]['id'],
                            'location_id': 9,
                            'company_id': 1,
                            'date_prod': date_prod,
                        })
                        tot += 1

                        row_machine_ok.append(i)

                    else:
                        parc_machine_id = sock.execute(dbname, uid, pwd, 'parc_machine', 'create', {
                            'product_id': machine_id,
                            'lot_id': serial[0]['id'],
                            'partner_id': tier[0]['id'],
                            'location_partner': tier[0]['id'],
                            'location_id': 9,
                            'company_id': 1,
                            'date_prod': date_prod,
                            'date_guaranttee': fin_garantie,
                        })
                        tot += 1

                        row_machine_ok.append(i)

    i += 1

fich_.close()

fich_ = open("/var/lib/odoo/log_parc.txt", 'wb')

for machine in row_machine_ok:
    fich_.write("ligne cree : " + str(machine) + ' \n\b')

fich_.write('total : ' + str(tot))
