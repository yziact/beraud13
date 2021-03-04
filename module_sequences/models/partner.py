# -*- coding : utf-8 -*-

from openerp import models, api, fields

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    visible_note = fields.Char(string='Note Client sur tout document', translate=True)

