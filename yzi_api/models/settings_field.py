# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import UserError


class SettingsField(models.Model):
    _name = 'settings.field'
    _description = """
        Used in the API
        We use this model to know what are the required and readonly fields
    """

    model_id = fields.Many2one(comodel_name='ir.model', required=True, string="Modèle")
    required_field_ids = fields.Many2many(comodel_name='ir.model.fields', string="Champs requis", relation="ir_model_fields_required_rel", column1="settings_field_id", column2="required_field_id")
    readonly_field_ids = fields.Many2many(comodel_name='ir.model.fields', string="Champs en lecture seule", relation="ir_model_fields_readonly_rel", column1="settings_field_id", column2="readonly_field_id")

    @api.model
    def create(self, vals):
        if 'required_field_ids' in vals and 'readonly_field_ids' in vals:
            rq_ids = vals.get('required_field_ids')[0][2]
            ro_ids = vals.get('readonly_field_ids')[0][2]

            for rq in rq_ids:
                if rq in ro_ids:
                    raise UserError("Un champ ne peut pas être obligatoire ET en lecture seule !")

        return super(SettingsField, self).create(vals)

    def write(self, vals):
        if 'required_field_ids' in vals or 'readonly_field_ids' in vals:
            rq_ids = vals.get('required_field_ids')[0][2] if 'required_field_ids' in vals else self.required_field_ids
            ro_ids = vals.get('readonly_field_ids')[0][2] if 'readonly_field_ids' in vals else self.readonly_field_ids

            for rq in rq_ids:
                if rq in ro_ids:
                    raise UserError("Un champ ne peut pas être obligatoire ET en lecture seule !")

        return super(SettingsField, self).write(vals)

    _sql_constraints = [
        ('model_uniq', 'unique(model_id)', 'Il y a déjà un enregistrement pour ce modèle !')
    ]
