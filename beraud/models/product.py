# -*- coding: utf-8 -*-

from openerp import models, api, fields
import openerp.addons.decimal_precision as dp
import datetime
import logging
_log = logging.getLogger(__name__)

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
            vals['supplier_taxes_id'] = [[6, False, [tax_supp[0], tax_supp[1]]]]

        if 'taxes_id' in vals:
            tax_code = tax_env.search_read(cr, uid, [('id', '=', vals['taxes_id'][0][2][0])])[0]
            tax_supp = tax_env.search(cr, 1, [('description', '=', tax_code['description'])])
            vals['taxes_id'] = [[6, False, [tax_supp[0], tax_supp[1]]]]

        res = super(ProductTemplate, self).create(cr, uid, vals, context)

        return res

    @api.multi
    def atom_cout_multi(self):
        prod_obj = self.pool.get('product.template')
        product_ids = prod_obj.search(self._cr, 13, [('standard_price', '=', 0.0)])
        print len(product_ids)

        for id in product_ids:
            prod = prod_obj.browse(self._cr, 13, [id])
            tarif = prod.tarif
            print tarif

            if tarif != 0.0:
                print "write : ", tarif
                prod.write({'standard_price': tarif})

    @api.multi
    def atom_cout_courant(self):
        prod_obj = self.pool.get('product.template')
        product_id = prod_obj.search(self._cr, 13, [('id', '=', self.id)])
        prod = prod_obj.browse(self._cr, 13, product_id)
        tarif = prod.tarif
        print tarif

        if tarif != 0.0:
            print "write : ", tarif
            prod.write({'standard_price': tarif})



class ProductCategory(models.Model):
    _inherit = "product.category"

    is_machine = fields.Boolean(string=u"Catégorie de machine")

class ProductProduct(models.Model):
    _inherit = "product.product"

    default_code = fields.Char('Internal Reference', select=True, required=True)

    def get_formview_id(self, cr, uid, id, context=None):
	print context
        try :
            view_id = self.pool.get('ir.ui.view').get_view_id(cr, uid,'beraud.product_template_inherit_form_view')
        except Exception:
            view_id = False
            _log.critical(u"la vue des product.product n'a pas ete trouvee")

        return view_id


    _sql_constraints = [
        ('unique_code',
         'UNIQUE(default_code)',
         'La reference doit etre unique')
    ]
