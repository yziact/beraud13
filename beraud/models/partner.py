from openerp import models, fields

class Partner(models.Model):
    _inherit = 'res.partner'

    # myCompany_id = fields.Many2one('res.company', "Company", select=1)
    #company_id = fields.Many2one(required=True)

