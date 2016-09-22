from openerp import api, models, fields

class account_paymennt_inherit(models.Model):
    _inherit = 'account.payment.term'

    type_sage = fields.Char('type sage')
