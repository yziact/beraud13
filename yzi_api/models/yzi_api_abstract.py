# -*- coding: utf-8 -*-

import ast

from werkzeug.exceptions import BadRequest

from odoo import models, api

from odoo.addons.base_rest.components.service import to_int, to_bool, to_float, to_datetime


class YziApiAbstract(models.Model):
    _name = 'yzi.api.abstract'
    _description = """
        Class to abtstract methods and validators of the API, and which provide helpful methods.
    """

    #### METHODS TO CREATE THE DICTS FOR VALIDATORS ####
    def create_dict_validator(self, model_name, with_required=False, with_readonly=False):
        """
        Create a dict with the field name in key, and the type in value, which will be used to check parameters
        Possibly the schema (for O2M and M2M), the allowed values (for selection) or coerce (int and bool)
        :param model_name: base model
        :param with_required: indicates if we must make fields required
        :param with_readonly: indicates if we must make fields readonly
        :return: the dict with constraints
        """
        fields_dict = {}
        required_fields = []
        readonly_fields = []

        # we get the model and its fields
        model_id = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)

        fields = self.env['ir.model.fields'].sudo().search([('model_id', '=', model_id.id)])

        for field in fields:
            # we get important datas for us
            allowed = schema = coerce = False

            if field.ttype == 'many2many' or field.ttype == 'one2many':
                type = 'list'
                schema = {
                    'type': 'integer'
                }
            elif field.ttype == 'text' or field.ttype == 'char' or field.ttype == 'html':
                type = 'string'
            elif field.ttype == 'reference' or field.ttype == 'selection':
                type = 'string'
                if field.selection:
                    selection = ast.literal_eval(field.selection)
                    allowed = [select[0] for select in selection]
            elif field.ttype == 'monetary' or field.ttype == 'float':
                type = 'float'
                coerce = to_float
            elif field.ttype == 'many2one':
                type = 'integer'
                coerce = to_int
            elif field.ttype == 'boolean':
                type = 'boolean'
                coerce = to_bool
            elif field.ttype == 'integer':
                type = 'integer'
                coerce = to_int
            elif field.ttype == 'datetime':
                type = 'datetime'
                coerce = to_datetime
            else:
                type = field.ttype

            fields_dict[field.name] = {'type': type}

            if allowed:
                fields_dict[field.name]['allowed'] = allowed
            if schema:
                fields_dict[field.name]['schema'] = schema
            if coerce:
                fields_dict[field.name]['coerce'] = coerce

            # creation of a list with the readonly fields in the ERP, to avoid modification of a readonly field
            if field.readonly:
                readonly_fields.append(field)

            # creation of a list with the required fields in the ERP, to avoid blocking in the ORM
            if field.required:
                required_fields.append(field)

        # if the function is called with the need to have the required fields
        # we call the corresponding function, and we give as extra the fields that the ERP requires
        fields_dict = self.required_dict_validator(fields_dict, model_name, required_fields) if with_required else fields_dict

        # if the function is called with the need to have the readonly fields
        # we call the corresponding function, and we give as extra the fields that the ERP readonly
        # else we return the dict
        return self.readonly_dict_validator(fields_dict, model_name, readonly_fields) if with_readonly else fields_dict

    def required_dict_validator(self, dict_fields, model_name, erp_required=[]):
        """
        Add required and empty keywords to the constraints dict
        :param dict_fields: base dict
        :param model_name: concerned model, on which we must search the required fields
        :param erp_required: extra required fields
        :return: the base dict with required and empty
        """
        required_fields = self.env['settings.field'].sudo().search([('model_id.model', '=', model_name)])

        if required_fields:
            erp_required.extend(required_fields.required_field_ids.filtered(lambda x: x.id not in [er.id for er in erp_required]))

        for field in erp_required:
            if field.name in dict_fields and 'required' not in dict_fields[field.name]:
                dict_fields[field.name]['required'] = True
                dict_fields[field.name]['empty'] = False

        return dict_fields

    def readonly_dict_validator(self, dict_fields, model_name, erp_readonly=[]):
        """
        Add readonly keyword to the constraints dict
        :param dict_fields: base dict
        :param model_name: concerned model, on which we must search the readonly fields
        :param erp_readonly: readonly fields
        :return: the base dict with readonly
        """
        readonly_fields = self.env['settings.field'].sudo().search([('model_id.model', '=', model_name)])

        if readonly_fields:
            erp_readonly.extend(readonly_fields.readonly_field_ids.filtered(lambda x: x.id not in [er.id for er in erp_readonly]))

        for field in erp_readonly:
            if field.name in dict_fields and 'readonly' not in dict_fields[field.name]:
                dict_fields[field.name]['readonly'] = True

        return dict_fields

    def create_return_dict_validator(self):
        """
        Method to check the returned values
        If returned values are not a simple dict (and so no verification), so the format is list of records and len of the list
        :return: the dict with constraints
        """
        return {
            'count': {'type': 'integer', 'required': True, 'empty': False},
            'rows': {'type': 'list', 'required': True, 'schema': {'type': 'dict'}}
        }

    #### USEFUL METHODS ####
    def check_field_existence(self, model_name, field_name):
        """
        Method which check if a field exists in a model
        :param model_name: concerned model
        :param field_name: field to search
        :return: possibly raise an error or True
        """
        model_id = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)

        if self.env['ir.model.fields'].sudo().search_count([('name', '=', field_name), ('model_id', '=', model_id.id)]) == 0:
            raise BadRequest("L'une des conditions concerne un champ qui n'existe pas")

        return True

    def check_fields_existence(self, model_name, fields_names):
        """
            Method which check if fields exist in a model
            :param model_name: concerned model
            :param fields_names: fields to search
            :return: possibly raise an error or True
            """
        model_id = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)

        for field_name in fields_names:
            if self.env['ir.model.fields'].sudo().search_count([('name', '=', field_name), ('model_id', '=', model_id.id)]) == 0:
                raise BadRequest("L'une des conditions concerne un champ qui n'existe pas")

        return True

    #### METHODS FOR PARAMS AND RESPONSES ####
    def _prepare_params(self, params):
        """
        The API expects a list for O2M and M2M fields
        To create or update, we use the syntax [(6, 0, [])]
        :param params: dict of datas
        :return: formatted params
        """
        for key, value in params.items():
            if type(value) is list:
                params[key] = [(6, 0, value)]

        return params

    def dict_json(self, record):
        """
        Method which transforms a record in a dict, to have readable values for JSON
        :param record: record that we must translate in JSON format
        :return: a dict with the record values
        """
        json_dict = {}

        fields_dict = record.fields_get()

        for name, field in fields_dict.items():
            if eval('record.' + name):
                # id and name (if exists) for M2O, O2M, M2M
                if field['type'] == 'many2one':
                    json_dict[name] = {
                        'id': eval('record.' + name + '.id')
                    }
                    sub_fields_dict = eval('record.' + name + ".fields_get()")
                    if 'name' in sub_fields_dict and sub_fields_dict['name']['type'] in ['char', 'text', 'html']:
                        json_dict[name]['name'] = eval('record.' + name + '.name')
                elif field['type'] == 'many2many' or field['type'] == 'one2many':
                    json_dict[name] = []
                    for sub_rec in eval('record.' + name):
                        element = {'id': sub_rec.id}
                        sub_fields_dict = sub_rec.fields_get()
                        if 'name' in sub_fields_dict and sub_fields_dict['name']['type'] in ['char', 'text', 'html']:
                            element['name'] = sub_rec.name

                        json_dict[name].append(element)
                # if binary, change it in string
                elif field['type'] == 'binary':
                    json_dict[name] = eval('record.' + name).decode('utf-8') if type(eval('record.' + name)) is bytes else eval('record.' + name)
                # if other, the value
                else:
                    json_dict[name] = eval('record.' + name)

        return json_dict

    #### MAIN METHODS ####
    def abstract_get(self, model, id=False):
        """
        Abstract method to get a record
        :param model: concerned model
        :param id: id to browse
        :return: a record or all the records of the model
        """
        return self.env[model].sudo().browse(id) if id else self.env[model].search([])

    def abstract_get_inactive(self, model):
        """
        Abstract method to get inactive records
        :param model: concerned model
        :return: all the inactive records of the model
        """
        return self.env[model].sudo().search([('active', '!=', True)]) if self.check_field_existence(model, 'active') else []

    def abstract_search(self, model, params):
        """
        Abtract method to search records with criterias
        :param model: concerned model
        :param params: research criterias
        :return: the result of search
        """
        domain = []

        for key, value in params.items():
            self.check_field_existence(model, key)

            # we change the operator according to the field type or name
            if key == 'name':
                domain.append((key, 'ilike', value))
            elif type(value) is list:
                domain.append((key, 'in', value))
            elif key == 'active' and value == False:
                domain.append((key, '!=', True))
            else:
                domain.append((key, '=', value))

        return self.env[model].sudo().search(domain)

    def abstract_create(self, model, params):
        """
        Abstract method to create a record
        :param model: concerned model
        :param params: values of the record
        :return: result of the creation
        """
        # we check that the given fields exist
        self.check_fields_existence(model, params.keys())

        # then we create the record after preparing params
        return self.env[model].sudo().create(self._prepare_params(params))

    def abstract_update(self, model, id, params):
        """
        Abstract method to update a record
        :param model: concerned model
        :param id: id of the record to update
        :param params: new values of the record
        :return: the record
        """
        # we check that the given fields exist
        self.check_fields_existence(model, params.keys())

        # we get the record and update
        record = self.abstract_get(model, id)
        record.write(self._prepare_params(params))

        return record

    def abstract_delete(self, model, id):
        """
        Abstract method to delete a record
        :param model: concerned model
        :param id: id of the record to delete
        :return: the deleted record
        """
        record = self.abstract_get(model, id)
        rec_dict = self.dict_json(record)

        record.unlink()

        return rec_dict

    def abstract_custom(self, model, id, params):
        """
        Method to call a function
        :param model: concerned model
        :param params: params that must contain the method name, and if needed, the parameters of the method
        :return: result of the function
        """
        if 'method' not in params:
            raise BadRequest("Vous devez préciser la méthode à appeler dans les paramètres avec le mot clé 'method'")

        method_params = ""
        for key, param in params.items():
            method_params = method_params + key + "=" + param + "," if key != 'method' else method_params

        # we delete the last ,
        arguments = method_params[0:-1] if method_params != "" else ""

        if not id:
            return eval("self.env['" + model + "']." + params.get('method') + "(" + arguments + ")")
        else:
            return eval("self.env[model].browse(id)." + params.get('method') + "(" + arguments + ")")
