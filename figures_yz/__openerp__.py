# -*- coding: utf-8 -*-
{
    'name': "Chiffres clefs",
    'author': "Yziact",
    'website': "http://www.yziact.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'sale',
        'account',
        'sales_team',
        'sale_crm',
        'report',
    ],

    # always loaded
    'data': [
        'views/view.xml',
    ],
}

