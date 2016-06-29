from openerp import models, api, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    background_color = fields.Char('Code hexa colour de fond')
    border_color = fields.Char('Code hexa couleur de bordure')
