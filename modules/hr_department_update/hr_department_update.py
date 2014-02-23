# -*- coding: utf-8 -*-
from osv import fields, osv


class hr_department(osv.osv):
    _name = "hr.department"
    _inherit = "hr.department"
    _order = 'company_id desc'

    _columns = {
        'responsible_directors': fields.many2one('res.users', 'Ответственный директор'),
        'department_time': fields.selection(
            [
                ('ua', u'Украина'),
                ('rus', u'Россия'),
                ('eu', u'ЕС')
            ], 'Рабочее время'),
    }

    _defaults = {
        'department_time': 'ua',
    }

hr_department()
