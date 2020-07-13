# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.base_rest.components.service import skip_secure_params

# variable used in all the functions, to call the model that makes the operations
ENV_HELP = "self.env['yzi.api.abstract']"


class AbstractService(Component):
    _inherit = 'base.rest.service'
    _name = 'abstract.service'
    _usage = 'abstract'
    _collection = 'yzi.private.services'
    _description = """
        Abstract service
        This service is used for all the models. Instead of use the word abstract, we replace it with the technical model name.
        The name of the model is transmitted to this service, which make the different actions.
    """

    #### MAIN METHODS ####
    def get(self, _model, _id=False):
        """
        Method to get a record
        :param _model: concerned model
        :param _id: id of the record
        :return: a dict with records and its count
        """
        records = eval(ENV_HELP).abstract_get(_model, _id)

        return {
            'count': len(records),
            'rows': [self._to_json(record) for record in records]
        }

    def get_inactive(self, _model):
        """
        Method to get inactive records
        :param _model: concerned model
        :return: a dict with records and its count
        """
        records = eval(ENV_HELP).abstract_get_inactive(_model)

        return {
            'count': len(records),
            'rows': [self._to_json(record) for record in records]
        }

    def search(self, _model, **params):
        """
        Method to find records with criterias
        :param _model: concerned model
        :param params: research criterias
        :return: a dict with records and its count
        """
        records = eval(ENV_HELP).abstract_search(_model, params)

        return {
            'count': len(records),
            'rows': [self._to_json(record) for record in records]
        }

    def create(self, _model, **params):
        """
        Method to create a record
        :param _model: concerned model
        :param params: datas for creation
        :return: a dict with the new record
        """
        return self._to_json(eval(ENV_HELP).abstract_create(_model, params))

    def update(self, _id, _model, **params):
        """
        Method to update a record
        :param _id: id of the record
        :param _model: concerned model
        :param params: new values
        :return: a dict with the updated record
        """
        return self._to_json(eval(ENV_HELP).abstract_update(_model, _id, params))

    def delete(self, _model, _id):
        """
        Method to delete a record
        :param _model: concerned model
        :param _id: id of the record
        :return: dict with a confirmation message
        """
        return eval(ENV_HELP).abstract_delete(_model, _id)

    @skip_secure_params
    def custom(self, _model, _id=False, **params):
        """
        Method to call a function
        :param _model: concerned model
        :param params: params that must contain the method name, and if needed, the parameters of the method
        :return: dict with the result of the function
        """
        return {
            'model': _model,
            'method': params.get('method', False),
            'result': str(eval(ENV_HELP).abstract_custom(_model, _id, params))
        }

    #### VALIDATION METHODS ####
    def _validator_search(self, **model):
        """
        Method which define the criterias that make parameters correct (mainly types, authorized values in selection...)
        For a search method
        :param model: extra params with the concerned model
        :return: a dict with the criterias
        """
        return eval(ENV_HELP).create_dict_validator(model.get('model', False))

    def _validator_create(self, **model):
        """
        Method which define the criterias that make parameters correct (mainly types, authorized values in selection...), and if they are required
        For a create method
        :param model: extra params with the concerned model
        :return: a dict with the criterias
        """
        return eval(ENV_HELP).create_dict_validator(model.get('model', False), True, True)

    def _validator_update(self, **model):
        """
        Method which define the criterias that make parameters correct (mainly types, authorized values in selection...)
        For an update method
        :param model: extra params with the concerned model
        :return: a dict with the criterias
        """
        return eval(ENV_HELP).create_dict_validator(model.get('model', False), False, True)

    # RETURN VALIDATORS
    def _validator_return_search(self, **model):
        """
        Method which check the output of the function called in API
        For a search method
        :param model: extra params with the concerned model, not used yet
        :return: a dict with the format of the output
        """
        return eval(ENV_HELP).create_return_dict_validator()

    def _validator_return_get(self, **model):
        """
        Method which check the output of the function called in API
        For a get method
        :param model: extra params with the concerned model, not used yet
        :return: a dict with the format of the output
        """
        return eval(ENV_HELP).create_return_dict_validator()

    #### PRIVATE METHOD ####
    def _to_json(self, record):
        """
        Method which transform a record in dict, which can be cast in JSON
        :param record: record to transform
        :return: a dict with record values
        """
        return eval(ENV_HELP).dict_json(record)