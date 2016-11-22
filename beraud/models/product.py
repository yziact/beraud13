# -*- coding: utf-8 -*-

from openerp import models, api, fields
import openerp.addons.decimal_precision as dp
import datetime

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # code_douane = fields.Char('Code douane')

    description_purchase= fields.Html('Purchase Description', translate=True)
    description_sale = fields.Html('Sale Description', translate=True)
    description_picking = fields.Html('Picking Description', translate=True)

    nb_palette = fields.Integer('Nombre de palettes')
    emplacement = fields.Char(string='Emplacement Beraud')
    emplacement_atom = fields.Char(string='Emplacement Atom')
    tarif = fields.Float('tarif', digits_compute=dp.get_precision('Product Price'))

    create_date = fields.Datetime('Create Date', readonly=True)

    property_account_income_id = fields.Many2one('account.account', company_dependent=False,
                                                 string="Income Account", oldname="property_account_income",
                                                 domain=[('deprecated', '=', False)],
                                                 help="This account will be used for invoices instead of the default one to value sales for the current product.")
    property_account_expense_id = fields.Many2one('account.account', company_dependent=False,
                                                  string="Expense Account", oldname="property_account_expense",
                                                  domain=[('deprecated', '=', False)],
                                                  help="This account will be used for invoices instead of the default one to value expenses for the current product.")

    # remove 'translate=True' from product template name
    name = fields.Char('Name', required=True, select=True)

    def create(self, cr, uid, vals, context=None):
        tax_env = self.pool.get('account.tax')

        if 'supplier_taxes_id' in vals:
            tax_code = tax_env.search_read(cr, uid, [('id', '=', vals['supplier_taxes_id'][0][2][0])])[0]
            tax_supp = tax_env.search(cr, 1, [('description', '=', tax_code['description'])])
            vals['supplier_taxes_id'] = [[6, False, [tax_supp[0]]], [6, False, [tax_supp[1]]]]

        if 'taxes_id' in vals:
            tax_code = tax_env.search_read(cr, uid, [('id', '=', vals['taxes_id'][0][2][0])])[0]
            tax_supp = tax_env.search(cr, 1, [('description', '=', tax_code['description'])])
            vals['taxes_id'] = [[6, False, [tax_supp[0]]], [6, False, [tax_supp[1]]]]

        res = super(ProductTemplate, self).create(cr, uid, vals, context)

        return res

class ProductCategory(models.Model):
    _inherit = "product.category"

    is_machine = fields.Boolean(string=u"Catégorie de machine")

class ProductProduct(models.Model):
    _inherit = "product.product"

    default_code = fields.Char('Internal Reference', select=True, required=True)

    _sql_constraints = [
        ('unique_code',
         'UNIQUE(default_code)',
         'La reference doit etre unique')
    ]
