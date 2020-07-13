# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_custom(cls):
        """
        Define the user that send the request
        If there is a correct cookie in the request, a correct uid is in the session
        Else we can't access to Odoo
        """
        # we take the session uid and add it to the request, so the the rules are applied
        request.uid = request.session.uid
