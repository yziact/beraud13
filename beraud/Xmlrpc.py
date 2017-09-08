#!/usr/bin/python
# -*- coding: utf-8 -*-

import xmlrpclib
import csv
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

username = "admin"
pwd = "X200yziact"
dbname = "BERAUD_PROD"

# Connexion Odoo
sock_common = xmlrpclib.ServerProxy("http://192.168.100.236:8069/xmlrpc/common")
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy("http://192.168.100.236:8069/xmlrpc/object")

fich_ = open('mu.csv', 'rb')

csvreader = csv.reader(fich_, delimiter=';')

tot = 0

for row in csvreader:
    if row[0] == "ID":
        continue

    task_id = int(row[0])
    task_type_id = 56

    project_task = sock.execute(dbname, uid, pwd, 'project.task', 'write', [task_id], {'stage_id': task_type_id})
