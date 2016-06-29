# -*- coding: utf-8 -*-
{
    'name': "beraud",

    'summary': """
        Module beraud """,

    'description': """
        Module beraud
    """,

    'author': "Yziact",
    'website': "http://www.yziact.fr",

    'category': 'Specific Industry Applications',
    'version': '0.1',

    'depends': [
        'base',
        'product',
        'stock',
        'mrp',
        'project_issue_sheet',
        'project_issue',
        'project',
    ],

    'data': [
        'views/res_partner.xml',
        'views/stock_view.xml',
        'views/product_view.xml',
        'views/transfer_stock_intercompany_view.xml',
        'views/analytic_line_task.xml',
        'views/analytic_line_issue.xml',
        'views/internal_invoice.xml',

        'report/layout/external_layout_header.xml',
        'report/layout/external_layout_footer.xml',
        'report/repair/report_mrprepairorder.xml',
        'report/stock/report_picking.xml',
        'report/stock/report_shipping2.xml',
        'report/sale/report_sale.xml',
        'report/invoice/report_invoice.xml',
    ],
}
