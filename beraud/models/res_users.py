# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _

class ResUsers(models.Model):
    _inherit = "res.users"

    main_company = fields.Many2one('res.company', u'Société Principale')
