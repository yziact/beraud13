# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CompanyInvoiceTime(models.TransientModel):
    name = 'company.invoice.time'

    date = fields.Date('Date de fin')

    def get_timiesheets(self):
        timesheets = False
        if self.date:
            timesheets = self.env['account.analytic.line'].search([
                ('move_id', '=', False),
                ('date', '<', self.date)]
            )
        return timesheets

    def get_time_to_invoice_per_company(self, timesheets):
        """
        Return dict like {'company_name', [list of timesheet_ids], 'company_one': [12,15,98,966]}
        :param timesheets:
        """
        companies = self.env['res.company'].search([])

        total = {}

        for company in companies:
            for time in timesheets:
                if time.task_id:
                    project_id = time.task_id.project_id
                    if project_id.company_id and project_id.company_id != company:
                        total[company].append(time.id)

                if time.project_id:
                    project_id = time.task_id.project_id
                    if project_id.company_id and project_id.company_id != company:
                        total[company].append(time.id)
                if time.repair_id:
                    if time.repair_id.company_id and time.repair_id.company_id != company:
                        total[company].append(time.id)
                if time.ticket_id:
                    if time.ticket_id.company_id and time.ticket_id.company_id != company:
                        total[company].append(time.id)

    def create_invoice_timesheet(self):
        print("coucou")

    def action_wizard(self):
        action = {
            'name': "Générer les factures internes",
            'type': "ir.actions.act_window",
            'target': 'current',
            'view_type': 'form',
            'views': [[False, "list"], [False, "form"]],
            'res_model': 'company.invoice.time',
            'view_id': self.env.ref('time_invoiced_by_companies.wizard_company_invoice_time').id,
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'default_partner_id': self.partner_id.id
            }
        }

        return action
