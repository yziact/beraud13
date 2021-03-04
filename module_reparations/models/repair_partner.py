# -*- coding: utf-8 -*-

from openerp.osv import fields, osv

class ResPartner_RepairInherit(osv.osv):
    _inherit = 'res.partner'

    def _repair_order_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x, 0), ids))
        # The current user may not have access rights for sale orders
        try:
            for partner in self.browse(cr, uid, ids, context):
                res[partner.id] = len(partner.repair_order_ids) + len(partner.mapped('child_ids.repair_order_ids'))
        except:
            pass
        return res


    _columns = {
        'repair_order_count' : fields.function(_repair_order_count, string=u"# d'ordre de réparation", type='integer'),
        'repair_order_ids' : fields.one2many('mrp.repair', 'partner_id', 'Repair Order')
    }


