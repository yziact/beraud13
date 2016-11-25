# -*- coding: utf-8 -*-
{
    'name': "Module Stocks",

    'summary': """
        Module Stocks Beraud """,

    'description': """
        Module Stocks Beraud
    """,

    'author': "Yziact",
    'website': "http://www.yziact.fr",

    'category': 'Specific Industry Applications',
    'version': '0.1',

    'depends': [
        'stock',
        'sale',
        'sale_stock',
        'sale_order_dates',
        'mrp',
        'product',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/stock_view.xml',
        'views/transfer_stock_intercompany_view.xml',
        'views/stock_picking.xml',
        'views/sale_order.xml',

        'reports/stock_reports.xml',
        'reports/report_picking.xml',
        'reports/report_shipping2.xml',

    ],

}

