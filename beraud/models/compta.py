from openerp import api, models, fields

class account_paymennt_inherit(models.Model):
    _inherit = 'account.payment.term'

    type_sage = fields.Char('type sage')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice.line'

    name = fields.Html(string='Description', required=True)

    @api.v8
    def get_invoice_line_account(self, type, product, fpos, company):

        account_env = self.env['account.account']
        partner_company_id = company.id
        accounts = product.product_tmpl_id.sudo().get_product_accounts(fpos)

        if type in ('out_invoice', 'out_refund'):
            account_id = account_env.search([('code', '=', accounts['income'].code), ('company_id', '=', partner_company_id)])
            account_id = fpos.map_account(account_id)
            return account_id

        account_id = account_env.search([('code', '=', accounts['expense'].code), ('company_id', '=', partner_company_id)])
        account_id = fpos.map_account(account_id)
        return account_id
