# -*- coding: utf-8 -*-

from odoo.addons.base_rest.controllers import main


class YziPrivateApiController(main.RestController):
    _root_path = '/yzi_api/'
    _collection_name = 'yzi.private.services'
    _default_auth = 'custom'
