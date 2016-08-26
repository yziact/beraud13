from openerp import models, api, fields


class Res_Partner_Inherit(models.Model):
    _inherit = 'res.partner'

    is_principal = fields.Boolean(string="contact principal")
    principal_contact = fields.Many2one('res.partner', compute='_get_principal_contact')


    def _get_principal_contact(self):
        for partner in self:
            principal = self.search([("parent_id",'=', partner.id),('is_principal','=',True)], limit=1)
            partner.principal_contact = principal
