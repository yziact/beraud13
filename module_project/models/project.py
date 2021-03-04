# -*- coding: utf-8 -*-
from openerp import models, api, fields


class ProjectInherit(models.Model):
    _inherit = 'project.project'

    tag_ids = fields.Many2many(string='Tags',
                               comodel_name='product.tag',
                               relation='product_project_tag_rel',
                               column1='tag_id',
                               column2='project_id')


class ProjectIssues(models.Model):
    _inherit = 'project.issue'

    description = fields.Html('Private Note')


class ProjectTask(models.Model):
    _inherit='project.task'


    @api.depends('stage_id')
    def stage_change(self):

        for task in self :
            print "TASK : ", task
            print "TASK STAGE : ", task.stage_id
            task.stage_copy = task.stage_id

            if task.stage_id.closed:
                print "TASK CLOSED"
                repair = self.env['mrp.repair'].search([('task_id', '=', task.id)])
                print "REPAIR : ", repair
                if repair:
                    task.action_send_signal()


    stage_copy = fields.Char('Stage copy', compute=stage_change, store=True)
    repair_state = fields.Boolean(string=u"Satut de la Réparation ", default=False)




