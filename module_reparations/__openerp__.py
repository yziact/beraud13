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
    ],

    'data': [
        'views/reparations_reports.xml',
        'views/repair_views.xml',

        'security/ir.model.access.csv',

        'reports/layout/external_layout_header.xml',
        'reports/layout/external_layout_footer.xml',
        'reports/repair/report_mrprepairorder.xml',
        'reports/repair/report_mrprepairorder_no_prices.xml',
    ],
}

