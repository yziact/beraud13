# -*- coding: utf-8 -*-
{
    'name': "Module Achats",

    'summary': """
        Module Achats Beraud """,

    'description': """
        Module Achats Beraud
    """,

    'author': "Yziact",
    'website': "http://www.yziact.fr",

    'category': 'Specific Industry Applications',
    'version': '0.1',

    'depends': [
        'base',
        'purchase',
    ],

    'data': [
        'security/ir.model.access.csv',

        'purchase_reports.xml',
        'reports/docs/report_purchase.xml',

        'views/purchase_views.xml',
    ],
}

