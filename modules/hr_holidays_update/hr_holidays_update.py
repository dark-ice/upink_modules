# -*- coding: utf-8 -*-
from __future__ import print_function, division
from datetime import datetime, timedelta
import math
from openerp.osv.orm import Model

from osv import fields, osv
from openerp import tools
import pytz
from notify import notify


tzlocal = pytz.timezone(tools.detect_server_timezone())


class hr_employee(Model):
    _inherit = "hr.employee"
    _columns = {
        'start_date': fields.date(u'Дата выхода'),
        'holidays_ids': fields.one2many('hr.holidays', 'employee_id', u"Отпуска"),
    }

    _defaults = {
        'start_date': datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

hr_employee()


class hr_holidays(Model):
    _description = "Leave"
    _inherit = "hr.holidays"

    _states = [
        ('draft', u'Черновик'),
        ('revision', u'Доработка'),
        ('validate1', u'Утверждение у Руководителя'),
        ('validate', u'Визирование HR'),
        ('confirm', u'Утверждено'),
        ('cancel', u'Отмена')
    ]

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        if ids:
            data_ids = self.browse(cr, uid, ids, context)

            for data in data_ids:
                access = str()

                #  Автор
                if data.user_id and data.user_id.id == uid:
                    access += 'a'

                #  Руководитель ответственного
                if data.head_id and data.head_id.user_id and data.head_id.user_id.id == uid:
                    access += 'm'

                #  HR
                users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', '=', 14)], order='id')
                if uid in users_work:
                    access += 'h'

                val = False
                letter = name[6]
                if letter in access:
                    val = True

                res[data.id] = val
        return res

    _columns = {
        'cr_date': fields.datetime(u'Дата создания', readonly=True),
        'note_reason': fields.text(u'Причина подачи заявки не в срок'),
        'comment': fields.text(u'Комментарий'),
        'job_id': fields.related(
            'employee_id',
            'job_id',
            type='many2one',
            relation='hr.job',
            string=u'Должность',
            store=True
        ),
        'head_id': fields.related(
            'employee_id',
            'parent_id',
            type='many2one',
            relation='hr.employee',
            string=u'Руководитель',
            store=True
        ),
        'state': fields.selection(_states, 'State', readonly=True),

        #  Права
        'check_a': fields.function(
            _check_access,
            method=True,
            string=u"Проверка на автора",
            type="boolean",
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string=u"Проверка на руководитель автора",
            type="boolean",
            invisible=True
        ),
        'check_h': fields.function(
            _check_access,
            method=True,
            string=u"Проверка на hr",
            type="boolean",
            invisible=True
        ),
        'get_days': fields.char(u'Доступные дни', size=5, readonly=True),
        'timedelt': fields.integer(u'Количество дней между подачей завления и началом отпуска', invisible=True),
        'history_ids': fields.one2many('hr.holidays.history', 'holiday_id', u'История переходов'),
    }

    _defaults = {
        'job_id': lambda self, cr, uid, context: self.pool.get('hr.employee').get_employee(cr, uid, uid).job_id.id,
        'head_id': lambda self, cr, uid, context: self.pool.get('hr.employee').get_employee(cr, uid, uid).parent_id.id,
        'cr_date': lambda *a: datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'name': lambda self, cr, uid, context: self.pool.get('hr.employee').get_employee(cr, uid, uid).name,
        'check_a': lambda *a: True,
        'get_days': lambda *a: "0",
    }

    def onchange_sec_id(self, cr, uid, ids, status, employee_id, context=None):
        obj_holiday_status = self.pool.get('hr.holidays.status')
        days = 0
        if status:
            days = obj_holiday_status.get_days(cr, uid, [status], employee_id, False, context)[status]['max_leaves']
        return {'value': {'get_days': days}}

    def get_state(self, state):
        return [item for item in self._states if item[0] == state][0]

    def onchange_date_from(self, cr, uid, ids, date_to, date_from, cr_date):
        result = {}
        if date_to and date_from:
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value'] = {
                'number_of_days_temp': round(diff_day) + 1,
                'timedelt': round(self._get_number_of_days(cr_date, date_from)) + 1
            }
            return result
        result['value'] = {
            'number_of_days_temp': 0,
            'timedelt': 0,
        }
        return result

    def workflow_setter(self, cr, uid, ids, state='draft'):
        return self.write(cr, uid, ids, {'state': state})

    @notify.msg_send(_inherit)
    def write(self, cr, uid, ids, values, context=None):
        data = self.browse(cr, uid, ids)[0]

        next_state = values.get('state', False)
        state = data.state

        if next_state and next_state != state:
            values.update({'history_ids': [(0, 0, {
                'usr_id': uid,
                'state': self.get_state(next_state)[1]
            })]})
            
        return super(hr_holidays, self).write(cr, uid, ids, values, context)

    def _check_available_days(self, cr, uid, ids):
        holidays_status_pool = self.pool.get('hr.holidays.status')
        for record in self.browse(cr, uid, ids):
            max_leaves = holidays_status_pool.get_days(
                cr,
                uid,
                [record.holiday_status_id.id],
                record.employee_id.id,
                False)[record.holiday_status_id.id]['max_leaves']
            if record.number_of_days_temp > max_leaves and not record.holiday_status_id.limit\
               and record.state == 'validate1':
                return False
            return True

    def _check_revision_comment(self, cr, uid, ids):
        for record in self.browse(cr, uid, ids):
            if record.state == 'revision' and not record.notes:
                return False
            return True

    _constraints = [
        (_check_available_days,
         'Нельзя взять отпуск на большее количество дней чем доступно',
         []),
        (_check_revision_comment,
         'Необходимо заполнить комментарий на доработку',
         [u'Комментарий на доработку']),
    ]

hr_holidays()


class hr_holidays_status(Model):
    _inherit = "hr.holidays.status"

    _columns = {
        'days': fields.text(u"Количество выделяемых дней"),
        'constant': fields.boolean(u"Постоянное значение"),
        'year_refresh': fields.boolean(u"Выдается каждый год"),
    }

    def get_days(self, cr, uid, ids, employee_id, return_false, context=None):
        employee = self.pool.get('hr.employee').browse(cr, uid, employee_id)
        holidays_pool = self.pool.get('hr.holidays')
        res = {}
        if employee.start_date:
            for record in self.browse(cr, uid, ids):
                res[record.id] = {}
                year = (datetime.now() - datetime.strptime(employee.start_date, "%Y-%m-%d")).days / 365
                leaves_taken = days = 0
                if year >= 1:
                    year = int(math.floor(year))
                if record.days:
                    formula_table = record.days.split(';')
                    for formula in formula_table:
                        exec formula

                domain = [
                    ('user_id', '=', uid),
                    ('holiday_status_id', '=', record.id),
                    ('state', '=', 'confirm')
                ]

                if record.year_refresh:
                    year_date = datetime.strptime(employee.start_date, "%Y-%m-%d") + timedelta(days=year*365)
                    domain.append(('date_from', '>=', year_date))

                holidays_ids = holidays_pool.search(
                    cr,
                    uid,
                    [
                        ('user_id', '=', uid),
                        ('holiday_status_id', '=', record.id),
                        ('state', '=', 'confirm')
                    ]
                )
                leaves_taken = sum([h.number_of_days for h in holidays_pool.browse(cr, uid, holidays_ids)])
                res[record.id]['max_leaves'] = days
                res[record.id]['leaves_taken'] = leaves_taken
                if record.constant:
                    remaining_leaves = 0
                else:
                    remaining_leaves = days - leaves_taken
                res[record.id]['remaining_leaves'] = remaining_leaves
        return res

hr_holidays_status()


class HolidaysHistory(Model):
    _name = 'hr.holidays.history'
    _description = u'Holidays - История переходов'
    _log_create = True
    _order = "create_date desc"
    _rec_name = 'state'

    _columns = {
        'usr_id': fields.many2one('res.users', u'Перевел'),
        'state': fields.char(u'На этап', size=65),
        'create_date': fields.datetime(u'Дата', readonly=True),
        'holiday_id': fields.many2one('hr.holidays', u'Holiday', invisible=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
    }

HolidaysHistory()
