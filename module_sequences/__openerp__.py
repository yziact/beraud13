# -*- coding: utf-8 -*-
{
    'name': "module_sequences",

    'summary': """
    Module Séquences pour Beraud.""",

    'description': """
    Module configurant les séquences pour Atom/Beraud.
    A installer avant de créer les entrepôts, car certaines séquences sont générées en même temps que la
    création de l'entrepôt.""",

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'sequences.xml',
    ],
}

