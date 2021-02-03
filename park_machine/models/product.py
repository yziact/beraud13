# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_machine = fields.Boolean()

    @api.onchange('categ_id')
    @api.depends('categ_id')
    def _set_is_machine(self):
        print('SETTING MACHINE')
        for product in self:
            is_machine = False
            if product.categ_id:
                if product.categ_id.is_machine_category:
                    is_machine = True
                else:
                    parent_cateroy_ids = self.env['product.category'].search([('is_machine_category', '=', True)])
                    machine_categ_ids = self.env['product.category'].search([
                        ('child_id', 'child_of', parent_cateroy_ids.ids)
                    ])
                    if product.categ_id.id in machine_categ_ids.ids:
                        is_machine = True
            product.write({'is_machine': is_machine})


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('categ_id')
    @api.depends('categ_id')
    def _set_is_machine(self):
        print('SETTING MACHINE - TMPL')
        for product_tmpl in self:
            for product in product_tmpl.product_variant_ids:
                is_machine = False
                if product.categ_id:
                    if product.categ_id.is_machine_category:
                        is_machine = True
                    else:
                        parent_cateroy_ids = self.env['product.category'].search([('is_machine_category', '=', True)])
                        machine_categ_ids = self.env['product.category'].search([
                            ('child_id', 'child_of', parent_cateroy_ids.ids)
                        ])
                        if product.categ_id.id in machine_categ_ids.ids:
                            print('hello')
                            is_machine = True
                product.product_variant_ids.write({'is_machine': is_machine})
