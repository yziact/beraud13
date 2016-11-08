# -*- coding: utf-8 -*-
{
    'name': "Module Facturation",

    'summary': """
        Module Facturation Beraud """,

    'description': """
        Module Facturation Beraud
    """,

    'author': "Yziact",
    'website': "http://www.yziact.fr",

    'category': 'Specific Industry Applications',
    'version': '0.1',

    'depends': [
        'base',
        'account',
        'beraud',
    ],

    'data': [
        'views/view_invoice.xml',

        'reports/report_invoice.xml',
    ],
}

