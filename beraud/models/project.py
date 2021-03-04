from openerp import models, api, fields

class ProjectProject(models.Model):
    _inherit = 'project.project'

    issue_ongoing_count = fields.Integer(compute="_compute_count")
    task_todo_count = fields.Integer(compute="_compute_count")

    @api.multi
    def _compute_count(self):
        for project in self:
            project.issue_ongoing_count = len(self.env['project.issue'].search([('project_id', '=', project.id),('stage_id.id', 'in', [52,53]),('stage_id.fold', '=', False)]))
            project.task_todo_count = len(self.env['project.task'].search([('project_id', '=', project.id),('stage_id.id', 'in', [47,48]),('stage_id.fold', '=', False)]))