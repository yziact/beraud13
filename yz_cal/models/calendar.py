from openerp import models, fields, api



class CalendarInherit(models.Model):
    _inherit = 'calendar.event'

    no_email = fields.Boolean(default=True)

    @api.model
    def create(self, vals, context):
        print vals
        print context
        res = super(CalendarInherit, self).create(vals, context)

        # return res
