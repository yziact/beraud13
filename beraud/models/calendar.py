from openerp import models, api, fields


class CalendarInherit(models.Model):
    _inherit = 'calendar.event'

    def create_attendees(self, cr, uid, ids, context=None):
        context['no_email'] = True

        res = super(CalendarInherit, self).create_attendees(cr, uid, ids, context=context)

        return res


    def create(self, cr, uid, vals, context=None):
        res = super(CalendarInherit, self).create(cr, uid, vals, context=context)

        return res
