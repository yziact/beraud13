# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import tools
from openerp.exceptions import UserError, AccessError

from openerp import models, api, fields

import logging 
_logger = logging.getLogger(__name__)

#class our_stock_change_product_qty(osv.osv_memory):
    #_inherit = "stock.stock_change_product_qty"
#    _inherit = "stock.change.product.qty"

#    def _prepare_inventory_line(self, cr, uid, inventory_id, data, context=None):

#        print "_prepare_inventory_line"
#        print "product_id : ", data.product_id
#        print "location_id : ", data.location_id
#        print "location_id.complete_name : ", data.location_id.complete_name
#        print "location_id.company_id : ", data.location_id.company_id

#        res = super(our_stock_change_product_qty, self)._prepare_inventory_line(cr, uid, inventory_id, data, context)
#        return res

class our_inventory(models.Model):
    
    _inherit = "stock.inventory"

    @api.multi
    def _default_company(self):
        if not self.location_id:
            raise UserError("location ID not defined while retrieving the default company_id")
        return self.location_id.company_id.id

    #'company_id': fields.many2one('res.company', 'Company', required=True, select=True, readonly=True, states={'draft': [('readonly', False)]}),
    company_id = fields.Many2one('res.company', related='location_id.company_id',
                                 required=True, select=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    #company_id = fields.Many2one('res.company', string='Company', default=_default_company,
    #                             required=True, select=True, readonly=True,
    #                             states={'draft': [('readonly', False)]})

class our_inventory_line(osv.osv):

    _inherit = 'stock.inventory.line'

    def _get_quants(self, cr, uid, line, context=None):
        quant_obj = self.pool["stock.quant"]

        dom = [('product_id','=',line.product_id.id), ('location_id','=',line.location_id.id)]
        #dom = [('product_id','=',line.product_id.id)]
        quants = quant_obj.search(cr, uid, dom, context=context)

        return quants


