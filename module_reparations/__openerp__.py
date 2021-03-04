# -*- coding: utf-8 -*-
{
    'name': "Module Reparations",

    'summary': """
        Module Reparations Beraud """,

    'description': """
        Module Reparations Beraud """,

    'author': "Yziact",
    'website': "http://www.yziact.fr",

    'category': 'Specific Industry Applications',
    'version': '0.1',

    'depends': [
        'base',
        'product',
        'stock',
        'mrp_repair',
        'beraud',

        # our modules
        'module_stocks',
    ],

    'data': [
        'views/reparations_reports.xml',
        'views/repair_views.xml',
        'views/partner_view.xml',
        'views/res_partner.xml',

        'security/ir.model.access.csv',
        'security/repair_security.xml',

        'reports/repair/report_mrprepairorder.xml',
        'reports/repair/report_mrprepairorder_no_prices.xml',
    ],
    #'test': [
    #    'test/test_repair.yml',
    #]
}

