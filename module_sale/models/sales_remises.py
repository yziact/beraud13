# -*- coding: utf-8 -*-

import calendar
from datetime import date
from dateutil import relativedelta
import json

from openerp import tools
from openerp import models, api, fields
from openerp.tools.float_utils import float_repr

import openerp.addons.decimal_precision as dp

from openerp.exceptions import UserError

code_loc = '[module_sale my_sales_remises]'

class my_sales_remises(models.Model):
    _inherit = 'sale.order.line'

    discount_amount = fields.Float(string="Discount Amount", digits=(16, 2), default=0.0)

    @api.onchange('product_uom_qty', 'price_unit')
    def onchange_product_uom_qty(self):
        print "[%s][%s] our onchange_product_uom_qty" % (__name__, code_loc)
        self.onchange_discount_amount()

    @api.onchange('discount_amount')
    def onchange_discount_amount(self):
        #super(my_sales_remises, self).onchange_partner_id()
        print "[%s][%s] our onchange_discount_amount" % (__name__, code_loc)
        total_price_ht = self.product_uom_qty * self.price_unit
        print "total price ht (qty*price_unit) = ", total_price_ht
        percent = 0.0
        
        try :
            percent = float(self.discount_amount*100)/float(total_price_ht)
        except ZeroDivisionError:
            print "[%s] divided by zero (total_price_ht), setting discount to zero" % (code_loc)

        self.discount = percent

    @api.onchange('discount')
    def onchange_discount(self):
        print "[%s][%s] our onchange_discount" % (__name__, code_loc)
        total_price_ht = self.product_uom_qty * self.price_unit
        amount_value = float(self.discount*total_price_ht)/100
        self.discount_amount = amount_value

