# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.exceptions import UserError, AccessError
from openerp.tools import float_compare


from openerp import models, api, fields
from lxml import etree
import logging
_logger = logging.getLogger(__name__)


class our_inventory(models.Model):
    _inherit = "stock.inventory"

    @api.multi
    def _default_company(self):
        if not self.location_id:
            raise UserError("location ID not defined while retrieving the default company_id")
        return self.location_id.company_id.id

    @api.onchange('line_ids', 'line_ids.cout_global')
    def _compute_total(self):
        print 'OUR COMPUTE TOTO'
        total = 0.0
        for line in self.line_ids:
            total += line.cout_global

        self.total = total

    company_id = fields.Many2one('res.company', related='location_id.company_id',
                                 required=True, select=True, readonly=True,
                                 states={'draft': [('readonly', False)]})

    total = fields.Float('Total', compute=_compute_total)

    #Overwrite de la function pour virer les consomables  de l inventaire
    def _get_inventory_lines(self, cr, uid, inventory, context=None):
        print "[%s] our _get_inventory_lines" % __name__

        location_obj = self.pool.get('stock.location')
        product_obj = self.pool.get('product.product')
        location_ids = location_obj.search(cr, uid, [('id', 'child_of', [inventory.location_id.id])], context=context)
        domain = ' location_id in %s'
        args = (tuple(location_ids),)

        if inventory.partner_id:
            domain += ' and owner_id = %s'
            args += (inventory.partner_id.id,)
        if inventory.lot_id:
            domain += ' and lot_id = %s'
            args += (inventory.lot_id.id,)
        if inventory.product_id:
            domain += ' and product_id = %s'
            args += (inventory.product_id.id,)
        if inventory.package_id:
            domain += ' and package_id = %s'
            args += (inventory.package_id.id,)

        # on ajout a la requete deux LEFT JOIN pour remonter aux product_template.type
        cr.execute('''
            SELECT q.id as quant_id, q.product_id, q.qty as product_qty, q.location_id, q.lot_id as prod_lot_id, q.package_id, q.owner_id as partner_id, t.emplacement, t.emplacement_atom
           FROM stock_quant q
            LEFT JOIN product_product p on p.id = q.product_id
            LEFT JOIN product_template t on t.id = p.product_tmpl_id
            WHERE t.type = 'product' AND ''' + domain + '''
           
        ''', args)
        #SELECT  q.product_id, sum(q.qty) as product_qty, q.location_id, q.lot_id as prod_lot_id, q.package_id, q.owner_id as partner_id, t.emplacement, t.emplacement_atom
        #GROUP BY product_id, location_id, lot_id, package_id, partner_id, emplacement, emplacement_atom
        #ORDER BY emplacement ASC

        vals = []

        for product_line in cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for key, value in product_line.items():
                if not value:
                    product_line[key] = False
            product_line['inventory_id'] = inventory.id
            product_line['theoretical_qty'] = product_line['product_qty']
            if product_line['product_id']:
                product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                product_line['product_uom_id'] = product.uom_id.id
            vals.append(product_line)

        return vals

    @api.multi
    def action_compute_cout(self):

        for inventory in self:
            for line in inventory.line_ids:
                line._compute_cout()

            inventory._compute_total()

    @api.model
    def fields_view_get(self, view_id=None, view_type=None, context=None, toolbar=False, submenu=False):
        print 'OUR FIELDS VIEW GET IN SALE CONTRACT'

        """
        Modification dynamique des valeurs envoyees a la vue
        """
        result = super(our_inventory, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=submenu)
        doc = etree.XML(result['arch'])
        params = self.env.context.get('params', False)

        if params:
            pass
            id = params.get('id', False)

            if id:
                record = self.env['stock.inventory'].browse(id)
                company_id = record.company_id.id

            node = doc.xpath("//tree")

        result['arch'] = etree.tostring(doc)
        return result


class our_inventory_line(osv.osv):
    _inherit = 'stock.inventory.line'
    _order = 'emplacement, emplacement_atom'

    def _get_quants(self, cr, uid, line, context=None):
        print("_GET_QUANTS")
        quant_obj = self.pool["stock.quant"]
        quants = []

        if line.quant_id:
            quants = [line.quant_id.id]

        if not quants:
            """
            dom = [('company_id', '=', line.company_id.id), ('location_id', '=', line.location_id.id),
                   ('lot_id', '=', line.prod_lot_id.id),
                   ('product_id', '=', line.product_id.id), ('owner_id', '=', line.partner_id.id),
                   ('package_id', '=', line.package_id.id), ('location_id', '=', line.location_id.id)]
            quants = quant_obj.search(cr, uid, dom, context=context)
            """

            dom = [('product_id', '=', line.product_id.id), ('location_id', '=', line.location_id.id)]
            quants = quant_obj.search(cr, uid, dom, context=context)

        return quants

    @api.depends('product_id', 'product_qty')
    def _compute_cout(self):
        print "OUR CDOMPUTE COST"

        for line in self:
            line.cout = line.product_id.product_tmpl_id.standard_price

            if line.product_qty >= 0:
                line.cout_global = line.product_id.product_tmpl_id.standard_price * line.product_qty
            else:
                line.cout_global = 0



    cout = fields.Float('Cout', type='float', compute=_compute_cout, store=True)
    cout_global = fields.Float('Cout global', compute=_compute_cout, type='float', store=True)
    emplacement = fields.Char('Emplacement')
    emplacement_atom = fields.Char('Emplacement')
    company_id = fields.Many2one('res.company')
    quant_id = fields.Many2one('stock.quant')
