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
        'product_dimension',
        'account',
        'report_intrastat',

        # our modules
        'module_report_filename',
        'module_sequences',
        'module_stocks',
        'module_reparations',
        'module_sale',
        'module_purchase',
        'module_project',
    ],

    'data': [
        'views/res_partner.xml',
        'views/company_view.xml',
        'views/product_view.xml',
        'views/analytic_line_task.xml',
        'views/analytic_line_issue.xml',
        'views/internal_invoice.xml',
        'views/parc_machine.xml',
        'views/product_category.xml',
        'views/export_sage.xml',
        'views/export_tier.xml',

        'security/ir.model.access.csv',

        'report/layout/external_layout_header.xml',
        'report/layout/external_layout_footer.xml',
        'report/invoice/report_invoice.xml',
        'report/invoice/sale_stock.xml',
    ],
}

