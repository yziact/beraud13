# -*- coding : utf-8 -*-

from openerp import models, api, fields

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    visible_note = fields.Char(string='Note Client sur tout document', translate=True)

    @api.model
    def get_nextref(self):
        return self.env['ir.sequence'].next_by_code('res.partner')

    @api.multi
    def set_ref(self):
        exist = []
        contacts = self.env['res.partner'].search([])

        for contact in contacts:
            if contact.ref:
                exist.append(str(contact.ref).replace(' ', ''))
                contact.ref = str(contact.ref).replace(' ', '')

        for contact in contacts:
            if not contact.ref:
                free = False
                while free != True:
                    ref = self.get_nextref()

                    if ref not in exist:
                        free = True
                # print ref

                contact.ref = ref

    @api.model
    def create(self, vals):
        """
        Genereration de la reference interne a la creation d'un nouveau contact
        """
        ref = self.get_nextref()
        vals['ref'] = ref
        return super(PartnerInherit,self).create(vals)

