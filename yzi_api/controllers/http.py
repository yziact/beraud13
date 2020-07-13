# -*- coding: utf-8 -*-

import json

from odoo.http import Controller, route, request, Response


class AuthController(Controller):

    @route('/yzi_api_auth', auth='public', methods=['POST'], csrf=False)
    def custom_auth(self, login='', password='', **params):
        """
        Authenticate a user
        Send session datas (including cookie) if correct login and password
        Else send a 401
        :param login: user login
        :param password: user password
        :param params: if other params
        :return: session datas or 401
        """
        try:
            request.session.authenticate(request.session.db, login, password)
        except:
            return Response("Accès refusé", status=401)

        return json.dumps(request.env['ir.http'].session_info())
