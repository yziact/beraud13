from openerp import models, api, fields


class CalendarInherit(models.Model):
    _inherit = 'calendar.event'

    def create_attendees(self, cr, uid, ids, context=None):
        print 'OUR CREATE ATTENDEES'
        print 'CONTEXT : ', context
        print 'NO MAIL : ', context.get('no_email')
        context['no_email'] = True


        res = super(CalendarInherit, self).create_attendees(cr, uid, ids, context=context)

        return res


    def create(self, cr, uid, vals, context=None):
        print 'OUR CREATE'

        print 'CONTEXT :', context

        res = super(CalendarInherit, self).create(cr, uid, vals, context=context)

        return res
