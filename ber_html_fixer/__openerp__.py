# -*- coding: utf-8 -*-
{
    'name': "Html Fixer pour Beraud",

    'summary': """
        Html Fixer pour Beraud """,

    'description': """
        Html Fixer pour Beraud """,

    'author': "G. Santos",

    'category': 'Sales',
    'version': '0.1',

    'depends': [
        'base', # for widgets
        'web', # for web.assets
        'sale', # for sale.order.line
    ],

    'data': [
        'insert.xml',
        'views/sale_order_line.xml',
    ],

    'qweb': [
        'static/src/xml/*.xml'
    ],
}

