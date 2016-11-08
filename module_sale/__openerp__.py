# -*- coding: utf-8 -*-
{
    'name': "Module des Ventes",

    'summary': """
    Module des Ventes pour Beraud.""",

    'description': """
    Module de la gestion des Ventes pour Béraud.""",

    'author': "Yziact",
    'website': "http://www.yziact.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/res_partner.xml',
        #'views/wizards.xml',

        'sale_reports.xml',
        'reports/report_sale.xml',

    ],

    # 'qweb': [
    #     'static/src/xml/templates.xml',
    # ]
}

