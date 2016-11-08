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

