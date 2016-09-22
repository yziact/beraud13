# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of mail_attach_existing_attachment,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     mail_attach_existing_attachment is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     mail_attach_existing_attachment is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with mail_attach_existing_attachment.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields_list):
        print "default get"
        res = super(MailComposeMessage, self).default_get(fields_list)
        print "fields_list : %s" % fields_list
        print "res : %s" % res

        if res.get('res_id') and res.get('model') and \
                res.get('composition_mode', '') != 'mass_mail' and\
                not res.get('can_attach_attachment'):
            res['can_attach_attachment'] = True  # pragma: no cover
        return res

    can_attach_attachment = fields.Boolean(string='Can Attach Attachment')
    object_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='mail_compose_message_ir_attachments_object_rel',
        column1='wizard_id', column2='attachment_id', string='Attachments')

    @api.multi
    def get_mail_values(self, res_ids):
        print "get mail values"
        res = super(MailComposeMessage, self).get_mail_values(res_ids)
        if self.object_attachment_ids.ids and self.model and len(res_ids) == 1:
            res[res_ids[0]].setdefault('attachment_ids', []).extend(
                self.object_attachment_ids.ids)
        return res

    @api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        print "OUR onchange_template_id"
        res = super(MailComposeMessage, self).onchange_template_id(template_id, composition_mode, model, res_id)

        print "MODEL : %s" % model
        print "res_id : %s" % res_id

        if model == 'sale.order':
            s_obj = self.env['sale.order'].browse(res_id)

            for line in s_obj.order_line:
                attach_recs = self.env['ir.attachment'].search([('res_name', 'ilike', line.product_id.name)])
                for i in attach_recs:
                    print "i.name : %s" % i.name
                    print "i.id : %s" % i.id
                    res['value']['attachment_ids'].append((4, i.id))
                
        return res


