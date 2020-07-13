{
    'name': 'API by Yziact',

    'summary': """
        Provide a REST API for Odoo
    """,

    'author': 'Yziact',

    "maintainers": ['C. CAPARROS'],

    'depends': [
        'base_rest',
        'component',
    ],

    'data': [
        'data/res_groups.xml',

        'views/settings_field.xml',

        'security/ir.model.access.csv'
    ],

}
