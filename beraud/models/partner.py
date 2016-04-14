from openerp import models, fields, api,

class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.many2one('res.company', 'Company', select=1, required=True)

