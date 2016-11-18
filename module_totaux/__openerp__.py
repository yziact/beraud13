# -*- coding: utf-8 -*-
{
    'name': "Module Totaux",

    'summary': """
    Module pour afficher les Totaux.""",

    'description': """
    Module pour afficher les Totaux sur les vues tree de Account Invoices,
    Sale Orders et Purchases """,

    'author': "Gabriel Santos - Yziact",
    'website': "http://www.yziact.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'sale', 'purchase', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/totals.xml',
    ],
}

