# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_use_fsm = fields.Boolean('Use Field service')
    is_use_repair = fields.Boolean('Use Repairs')
    is_use_helpdesk = fields.Boolean('Use helpdesk (ticket)')
    is_use_category_machine = fields.Boolean('Use categories')
