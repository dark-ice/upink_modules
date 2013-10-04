# -*- coding: utf-8 -*-
from osv import fields, osv


class hr_applicant(osv.osv):
    _name = "hr.applicant"
    _inherit = "hr.applicant"

    _columns = {
        'history_ids': fields.one2many('hr.applicant.history', 'applicant_id', 'История'),
        'attachment_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Вложения',
            domain=[('res_model', '=', 'hr.applicant')],
            context={'res_model': 'hr.applicant'}
        ),
    }

    def write(self, cr, uid, ids, values, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        data = self.browse(cr, uid, ids[0])

        next_state = values.get('stage_id', False)
        state = data.stage_id

        if next_state and next_state != state:
            values.update({'history_ids': [(0, 0, {
                'us_id': uid,
                'state': next_state
            })]})

        for attachment in values.get('attachment_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'hr.applicant'

        return super(hr_applicant, self).write(cr, uid, ids, values, context)

hr_applicant()


class applicant_history(osv.osv):
    _name = 'hr.applicant.history'
    _columns = {
        'us_id': fields.many2one('res.users', u'Перевел'),
        'create_date': fields.datetime(u'Дата и время'),
        'state': fields.char(u'На этап', size=65),
        'applicant_id': fields.many2one('hr.applicant', 'Applicant', invisible=True),
    }

    _order = "create_date desc"

applicant_history()
