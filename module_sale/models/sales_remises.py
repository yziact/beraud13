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

class my_sales_remises(models.Model):
    _inherit = 'sale.order.line'

    is_da = fields.Boolean(string="Make Amount Discount", default=False, store=True)
    discount_amount = fields.Float(string="Amount Discount", digits=(16, 2), default=0.0)
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    @api.onchange('discount_amount')
    def onchange_discount_amount(self):
        # if we are making a discount_amount set the percent.
        # If not, return
        print "[%s] our onchange_discount_amount" % __name__
        if not self.is_da:
            return

        print "calculating the discount based on the discount_amount"
        #super(my_sales_remises, self).onchange_partner_id()
        total_price_ht = self.product_uom_qty * self.price_unit
        print "total price ht (qty*price_unit) = ", total_price_ht
        percent = 0.0
        
        try :
            percent = float(self.discount_amount*100)/float(total_price_ht)
        except ZeroDivisionError:
            print "[%s] divided by zero (total_price_ht), setting discount to zero" % __name__

        self.discount = percent

        print "[%s] discount_amount is : %s " % (__name__, self.discount_amount)
        print "[%s] discount is : %s" % (__name__, self.discount)

    @api.onchange('discount')
    def onchange_discount(self):
        # if we are making a discount_amount,
        # don't modify the discount_amount
        print "[%s] our onchange_discount" % __name__
        if self.is_da:
            return

        print "calculating the discount_amount based on the discount"
        total_price_ht = self.product_uom_qty * self.price_unit
        amount_value = float(self.discount*total_price_ht)/100
        self.discount_amount = amount_value

        print "[%s] discount_amount is : %s " % (__name__, self.discount_amount)
        print "[%s] discount is : %s" % (__name__, self.discount)


