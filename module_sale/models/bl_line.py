# -*- coding: utf-8 -*-

from openerp import models, api, fields

class BlLine(models.Model):
    _name = "bl.line"

    invoice_id = fields.Many2one(comodel_name="account.invoice", readonly=1, string="Facture concernée")
    bl_id = fields.Many2one(comodel_name="stock.picking", string="Bon de livraison")
    to_print = fields.Boolean(default=True, readonly=0, string="Imprimer sur la facture")

    _sql_constraints = [
        ('unique_bl_on_invoice',
         'UNIQUE(invoice_id,bl_id)',
         'Le bon de livraison est déjà présent pour cette facture.')
    ]
