# -*- coding: utf-8 -*-
{
    'name': "Actions commerciales",

    'summary': """Actions commerciales""",

    'description': """Module de gestion des actions commerciales mennées de le cadre d'une CRM.""",

    'author': "Yziact",
    'website': "http://www.yziact.fr",

    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends':
        [
            'base',
            'sale',
            'crm',
            'mail',
            'sales_team',
            'calendar',
        ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'views/action.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/crm_lead.xml',
        'views/calendar_event.xml',

        'static/src/xml/backend.xml',
    ],
    'qweb': [
        'static/src/xml/sales_team_dashboard.xml',
    ],
}
