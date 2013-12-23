# -*- coding: utf-8 -*-
from __future__ import division
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta
import numpy
from openerp import tools
from openerp.osv import osv, fields
from openerp.osv.orm import AbstractModel, Model, browse_null
import pytz
from notify import notify
import decimal_precision as dp

tzlocal = pytz.timezone(tools.detect_server_timezone())
_logger = logging.getLogger(__name__)


def add_months(source, months):
    month = source.month - 1 + months
    year = source.year + int(month / 12)
    month = month % 12 + 1
    return month, year


class KpiPeriod(Model):
    _name = "kpi.period"
    _description = u"KPI - Период"
    _order = "year desc, month desc"

    def next(self, cr, period_id):
        try:
            period = self.browse(cr, 1, period_id)
            period_date = date(int(period.year), int(period.month), 3)
            next_month, next_year = add_months(period_date, 1)

            if next_month < 10:
                next_month = "0%s" % next_month
            next_period = "%s/%s" % (next_year, next_month)
            next_ids = self.search(cr, 1, [('name', '=', next_period), ('calendar', '=', period.calendar)])
            result = self.browse(cr, 1, next_ids[0])
            return result
        except IndexError:
            return browse_null()

    def get_by_date(self, cr, period_date, calendar='rus'):
        month, year = add_months(period_date, 0)
        if month < 10:
            month = "0%s" % month
        period = "%s/%s" % (year, month)
        next_ids = self.search(cr, 1, [('name', '=', period), ('calendar', '=', calendar)])
        if next_ids:
            return self.browse(cr, 1, next_ids[0])

    def _get_title(self, cr, uid, ids, field_name, field_value, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            month = record.month
            if month < 10:
                month = '0%s' % month
            result[record.id] = "%s/%s" % (record.year, month)
        return result

    _columns = {
        'name': fields.function(
            _get_title,
            type="char",
            store=True,
            method=True,
            string=u"Период",
            select=1,
            readonly=True
        ),
        'month': fields.integer(u'Месяц'),
        'year': fields.integer(u'Год'),
        'calendar': fields.selection(
            (
                ('rus', u'Россия'),
                ('ua', u'Украина'),
                ('eu', u'ЕС'),
            ), u'Тип календаря'),
        'days': fields.integer(u'Количество рабочих дней'),
    }

    def create(self, cr, uid, values, context=None):
        return super(KpiPeriod, self).create(cr, uid, values, context)

    def _check_month(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if record.month < 1 or record.month > 12:
                return False
            return True

    def _check_uniq_period(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if self.search(cr, uid, [('month', '=', record.month), ('id', '!=', record.id),
                                     ('year', '=', record.year), ('calendar', '=', record.calendar)]):
                return False
            return True

    _constraints = [
        (
            _check_month,
            'Месяц не может быть меньше 1 и больше 12',
            [u'Месяц']
        ),
        (
            _check_uniq_period,
            'Нельзя иметь более 1 периода на заданые месяц/год/тип календаря',
            [u'Месяц', u'Год', u'Тип календаря']
        )
    ]
KpiPeriod()


class KpiGrade(Model):
    _name = "kpi.grade"
    _description = u"KPI - Грейды и категории"
    _order = "name"

    _columns = {
        'name': fields.char(u'Грейд', size=20, required=True),
        'cash': fields.float(u'ЗП', digits=(10, 2)),
    }

    def _check_uniq_grade(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if self.search(cr, uid, [('name', '=', record.name), ('id', '!=', record.id)]):
                return False
            return True

    _constraints = [
        (
            _check_uniq_grade,
            'Нельзя иметь 2 одинаковых грейда',
            [u'Грейд']
        )
    ]
KpiGrade()


class hr_employee(Model):
    _inherit = "hr.employee"

    def grade_calculate(self, cr, user, ids, field_name, arg, context):
        current_date = date.today()
        res = {}
        for i in ids:
            grade_id, dy_cash = self.pool.get('kpi.grade.history').get_grade(cr, current_date, i)
            res[i] = {'grade_id': grade_id, 'dy_cash': dy_cash}
        return res

    _columns = {
        'formalized': fields.boolean('Официально оформлен'),
        'maternity': fields.boolean('В декретном отпуске'),
        'grade_id': fields.function(grade_calculate, type='many2one', multi='grade', obj="kpi.grade", method=True, string='Грейд'),
        'dy_cash': fields.function(grade_calculate, type='float', multi='grade', string="Сумма начисления", digits=(10, 2)),
        'grade_history_ids': fields.one2many('kpi.grade.history', 'employee_id', 'История изменения грейдов'),
        'retention_ids': fields.one2many('kpi.retention', 'employee_id', 'Удержания'),
        'award_ids': fields.one2many('kpi.award', 'employee_id', 'Премии'),
    }
hr_employee()


class KpiGradeHistory(Model):
    _name = "kpi.grade.history"
    _description = u"KPI/Сотрудники - История изменения грейда"
    _order = 'period_id desc, create_date desc'

    def get_period(self, cr, date, employee_id):
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        period_pool = self.pool.get('kpi.period')
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, 1, employee_id)
            period = period_pool.get_by_date(cr, date, employee.department_id.department_time or 'rus')
            return period

    def get_grade(self, cr, date, employee_id):
        period = self.get_period(cr, date, employee_id)
        history_ids = self.search(cr, 1, [('employee_id', '=', employee_id), ('period_id.name', '<=', period.name)])
        if history_ids:
            history_obj = self.read(cr, 1, history_ids[0], ['next_grade_id', 'next_dy_cash'])
            return history_obj['next_grade_id'][0], history_obj['next_dy_cash']
        return None, 0.0

    def _get_period(self, cr, uid, ids, name, arg, context=None):
        res = {}
        period_pool = self.pool.get('kpi.period')
        for record in self.browse(cr, uid, ids, context):
            period = self.get_period(cr, record.history_date, record.employee_id.id)
            next_period = period_pool.next(cr, period.id)
            res[record.id] = next_period.id
        return res

    _columns = {
        'grade_id': fields.many2one('kpi.grade', u'Грейд'),
        'next_grade_id': fields.many2one('kpi.grade', u'Грейд'),
        'history_date': fields.date(u'Вступает в силу с'),
        'employee_id': fields.many2one('hr.employee', u'Сотрудник'),
        'dy_cash': fields.float(u'Старое начисление'),
        'next_dy_cash': fields.float(u'Новое начисление'),
        'period_id': fields.function(
            _get_period,
            type="many2one",
            relation='kpi.period',
            string=u'Период с которого действует изменение',
            store=True),
        'create_uid': fields.many2one('res.users', u'Изменил грейд'),
        'create_date': fields.datetime(u'Дата изменения', readonly=True),
    }
KpiGradeHistory()


class KpiIndicatorsReference(Model):
    """
        Справочник ключевых показателей.
        @formula - вводится формула расчета показателя. При расчете конкретных
        показателей она будет скомпилирована (exec)
    """
    _name = 'kpi.indicators.reference'
    _description = u'KPI - Справочник ключевых показателей'

    _columns = {
        'name': fields.char(u'Название показателя', size=255, select="1", required=True),
        'units': fields.char(u'Единицы измерения', size=50, select="1", required=True),
        'formula': fields.text(u'Формула расчета', required=True),
        'index_type': fields.boolean(u'Перевыполняемый', select="1"),
        'active': fields.boolean(u'Активно'),
        'type': fields.selection(
            (
                ('mbo', 'MBO'),
                ('sla', 'SLA'),
                ('sale', 'Sale SLA'),
                ('sla-2', 'SLA-2'),
            ), u"Тип показателя", required=True
        )
    }

    _defaults = {
        'type': lambda s, c, u, cnt: cnt.get('from', False) or 'mbo',
    }
KpiIndicatorsReference()


class KpiStaff(AbstractModel):
    _name = "kpi.staff"
    _rec_name = "employee_id"
    _order = "period_id, employee_id"

    _columns = {
        'period_id': fields.many2one('kpi.period', u'Период'),
        'employee_id': fields.many2one('hr.employee', u'Сотрудник', required=True),
        'calendar': fields.related(
            'employee_id',
            'department_id',
            'department_time',
            type="char",
            size=3,
            string=u"Тип календаря",
            invisible=True
        )
    }

    _defaults = {
        'calendar': 'rus'
    }

    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        calendar = 'rus'
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context)
            calendar = employee.department_id.department_time
        return {'value': {'calendar': calendar}}

    def onchange_calendar(self, cr, uid, ids, calendar, period_id, context=None):
        period_pool = self.pool.get('kpi.period')
        if period_id:
            period = period_pool.browse(cr, uid, period_id, context)
            if period.calendar != calendar:
                period_ids = period_pool.search(cr, uid, [('name', '=', period.name), ('calendar', '=', calendar)])
                if period_ids:
                    return {'value': {'period_id': period_ids[0]}}

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        period_pool = self.pool.get('kpi.period')
        period = [item for item in args if item[0] == 'period_id']

        if period:
            if isinstance(period[0][2], (tuple, list)):
                period_id = period[0][2][0]
            else:
                period_id = period[0][2]
            period_name = period_pool.browse(cr, user, period_id)

            domain = [('name', '=', period_name.name)]

            need_period_ids = period_pool.search(cr, user, domain)
            if need_period_ids:
                args.remove(period[0])
                args.append(('period_id', 'in', need_period_ids))
        return super(KpiStaff, self).search(cr, user, args, offset, limit, order, context, count)


class KpiEnrollmentFormal(Model):
    _name = "kpi.enrollment.formal"
    _inherit = "kpi.staff"
    _description = u"KPI - Зачисление официальной ЗП"
    _auto = True

    _columns = {
        'employee_id': fields.many2one('hr.employee', u'Сотрудник', required=True, domain=[('formalized', '=', True)]),
        'cash': fields.float(u'Официальная ЗП', digits=(10, 2), required=True),
        'type': fields.selection(
            (
                ('formal', u'Официальная зарплата'),
                ('advance', u'Официальный аванс')
            ), u'Тип выплаты'
        )
    }

    def _check_uniq_award(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if self.search(cr, uid, [('period_id', '=', record.period_id.id), ('type', '=', record.type),
                                     ('employee_id', '=', record.employee_id.id), ('id', '!=', record.id)]):
                return False
            return True

    _constraints = [
        (
            _check_uniq_award,
            'Нельзя создавать 2 одинаковых оплаты на один период',
            []
        )
    ]
KpiEnrollmentFormal()


class KpiFormalTax(Model):
    _name = "kpi.formal.tax"
    _inherit = "kpi.staff"
    _description = u"KPI - Налог с официальной ЗП"
    _auto = True

    _columns = {
        'employee_id': fields.many2one('hr.employee', u'Сотрудник', required=True, domain=[('formalized', '=', True)]),
        'cash': fields.float(u'Налог', digits=(10, 2), required=True),
    }

    def _check_uniq_award(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if self.search(cr, uid, [('period_id', '=', record.period_id.id),
                                     ('employee_id', '=', record.employee_id.id), ('id', '!=', record.id)]):
                return False
            return True

    _constraints = [
        (
            _check_uniq_award,
            'Нельзя создавать 2 одинаковых оплаты на один период',
            []
        )
    ]
KpiFormalTax()


class KpiAdvance(Model):
    _name = "kpi.advance"
    _inherit = "kpi.staff"
    _description = u"KPI - Аванс"
    _auto = True

    _columns = {
        'cash': fields.float(u'Аванс', digits=(10, 2), required=True),
    }
KpiAdvance()


class KpiRetention(Model):
    _name = "kpi.retention"
    _inherit = "kpi.staff"
    _description = u"KPI - Удержания"
    _auto = True

    _columns = {
        'cash': fields.float(u'Сумма удержания', digits=(10, 2), required=True),
        'note': fields.text(u'Основания', required=True)
    }
KpiRetention()


class KpiAward(Model):
    _name = "kpi.award"
    _inherit = "kpi.staff"
    _description = u"KPI - Премии"
    _auto = True

    _columns = {
        'cash': fields.float(u'Сумма премии', digits=(10, 2), required=True),
        'note': fields.text(u'Основания', required=True)
    }

    def _check_uniq_award(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if self.search(cr, uid, [('period_id', '=', record.period_id.id),
                                     ('employee_id', '=', record.employee_id.id), ('id', '!=', record.id)]):
                return False
            return True

    _constraints = [
        (
            _check_uniq_award,
            'Нельзя создавать 2 премии на один период',
            []
        )
    ]
KpiAward()


class KpiSmart(Model):
    _name = "kpi.smart"
    _description = u"KPI - SMART"
    _order = "create_date DESC"

    _states = (
        ('draft', u'Черновик'),
        ('revision', u'Доработка'),
        ('agreement', u'Согласование с руководителем направления'),
        ('inwork', u'Задача поставлена'),
        ('delegated', u'Задача делегирована'),
        ('done', u'Задача выполнена'),
        ('accepted', u'Задача принята'),
        ('not_accepted', u'Задача не принята'),
        ('cancel', u'Отмена'),
        ('removed', u'Задача снята'),
        ('transfer', u'Перенос'),
        ('not_done', u'Не выполнена'),
    )

    def _get_plan(self, cr, period_id, employee_id):
        l = self.search(cr, 1, [
            ('period_id.id', '=', period_id),
            ('responsible_id.id', '=', employee_id),
            ('state', 'not in', ('transfer', 'cancel', 'removed', 'draft', 'agreement'))
        ], count=True)
        if l > 10:
            l = 10
        return l

    def _get_fact(self, cr, period_id, employee_id):
        return self.search(cr, 1, [
            ('period_id.id', '=', period_id),
            ('responsible_id.id', '=', employee_id),
            ('state', '=', 'accepted')
        ], count=True)

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        empl_pool = self.pool.get('hr.employee')
        res = {}
        for data in self.browse(cr, 1, ids, context):
            access = str()

            #  Автор
            if data and data.author_id and data.author_id.user_id.id == uid:
                access += 'a'

            #  Инициатор
            if data and data.initiator_id and \
                    ((data.initiator_id.user_id.id == uid and data.state == 'inwork')
                     or (empl_pool.get_department_manager(cr, uid, data.initiator_id.id, context).user_id.id == uid and data.state == 'done')):
                access += 'i'

            #  Ответственный
            if data and data.responsible_id and data.responsible_id.user_id.id == uid:
                access += 'r'

            #  Руководитель ответственного
            if data and data.responsible_head_id and data.responsible_head_id.user_id.id == uid:
                access += 'm'

            if data and data.responsible_head_id and data.author_id and data.responsible_head_id == data.author_id:
                access += 'e'

            if data and data.parent_id and data.parent_id.responsible_head_id and data.parent_id.responsible_head_id.user_id.id == uid:
                access += 'x'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[data.id] = val
        return res

    def _check_color(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            val = 'gray'
            if record.state == 'inwork':
                now = datetime.now(pytz.UTC)
                deadline = datetime.strptime(record.deadline_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
                if now > deadline:
                    val = 'red'
                elif (now + timedelta(days=3)) > deadline > now:
                    val = 'yellow'
                else:
                    val = 'green'
            if record.state == 'done':
                val = 'blue'

            res[record.id] = val
        return res

    def _create_kpi_mbo_smart(self, cr, user, kpi_id):
        mbo_pool = self.pool.get('kpi.mbo')
        kpi = self.pool.get('kpi.kpi').browse(cr, 1, kpi_id)
        smart_mbo_id = self.pool.get('kpi.indicators.reference').search(cr, user, [('name', 'ilike', 'SMART')])
        mbo_ids = mbo_pool.search(cr, user, [('name.id', '=', smart_mbo_id[0]), ('kpi_id.id', '=', kpi_id)])

        smart_plan = self._get_plan(cr, kpi.period_id.id, kpi.employee_id.id) or 0
        smart_fact = self._get_fact(cr, kpi.period_id.id, kpi.employee_id.id) or 0

        if not mbo_ids:
            mbo_pool.create(cr, 1, {
                'plan': smart_plan + 1,
                'fact': smart_fact,
                'kpi_id': kpi_id,
                'name': smart_mbo_id[0]
            })
        else:
            if smart_plan < 10:
                plan = smart_plan + 1
            else:
                plan = 10
            mbo_pool.write(cr, 1, mbo_ids[0], {'plan': plan, 'fact': smart_fact})

        return smart_plan, smart_fact

    def _show_number(self, cr, uid, ids, name, arg, context=None):
        data = self.browse(cr, uid, ids, context)
        result = {}
        i = 1
        for row in data:
            result[row.id] = i
            i += 1

        return result

    _columns = {
        'name': fields.char(
            'Задача',
            size=250,
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)], 'revision': [('readonly', False)]},
            help='Суть SMART-задачи.'),
        'author_id': fields.many2one(
            'hr.employee',
            string='Автор',
            readonly=True,
            states={'draft': [('readonly', False)], 'revision': [('readonly', False)]},
            help='Автор SMART-задачи.'),
        'initiator_id': fields.many2one(
            'hr.employee',
            string='Инициатор',
            readonly=True,
            states={'draft': [('readonly', False)], 'revision': [('readonly', False)]},
            help='Инициатор SMART-задачи.\n'
                 'Инициатор задачи на этапе "Задача поставлена" может либо снять либо'
                 ' перенести задачу. На этапе "Задача принята" может либо "Принять задачу"'
                 ' либо "Не принять"'),
        'responsible_id': fields.many2one(
            'hr.employee',
            string='Ответственный',
            required=False,
            readonly=True,
            states={'draft': [('readonly', False), ('required', True)]},
            help='Ответственный за выполнение задачи.'
                 ' В случае создания Smart-задачи из бланка KPI данное поле заполняется автоматически.\n'
                 'В случае создания Smart-задачи из модуля Smart-задач, поле заполняется вручную.'
                 ' Обязательное к заполнению'
        ),
        'responsible_head_id': fields.many2one(
            'hr.employee',
            readonly=True,
            states={'draft': [('readonly', False)], 'revision': [('readonly', False)]},
            string='Руководитель ответственного',
            help='Поле заполняется автоматически, в зависимости от выбранного ответственного.\n'
                 'Руководитель на этапе "Согласование с руководителем ответственного" может перевести задачу'
                 ' в Черновик, На доработку, либо Поставить задачу.\n'
                 'Руководитель на этапе "Задача поставлена" может либо снять либо перенести задачу'),
        'create_date': fields.datetime(
            'Дата создания',
            readonly=True,
            help='Дата создания SMART-задачи.'),
        'deadline_date': fields.datetime(
            'Срок выполнения',
            readonly=True,
            states={'draft': [('readonly', False)], 'revision': [('readonly', False)]},
            help='Срок выполнения SMART-задачи.'
                 ' В зависимости от установленного срока заполняется поле "Период" '),
        'deadline_check': fields.boolean(
            'Срок выполнения изменен',
            readonly=True,
            states={'draft': [('readonly', False)], 'revision': [('readonly', False)]},
            invisible=True),
        'note': fields.text(
            'Критерий выполнения',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)], 'revision': [('readonly', False)]},
            help='Параметры, по которым оценивается выполненная задача.'),
        'state': fields.selection(
            _states,
            'Статус',
            readonly=True,
            help='Темным цветом выделяется текущий этап задачи.'),
        'history_ids': fields.one2many(
            'kpi.smart.history',
            'smart_id',
            'История переходов',
            help='Таблица отображает историю смены этапов задачи.'),
        'period_id': fields.many2one(
            'kpi.period',
            'Период',
            readonly=True,
            help='Период KPI, к которому принадлежит данная задача.'),
        'calendar': fields.related(
            'responsible_id',
            'department_id',
            'department_time',
            type="char",
            size=3,
            string='Тип календаря',
            invisible=True
        ),

        'check_a': fields.function(
            _check_access,
            method=True,
            string='Проверка на автора',
            type='boolean',
            invisible=True
        ),
        'check_i': fields.function(
            _check_access,
            method=True,
            string='Проверка на инициатора',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Проверка на ответственного',
            type='boolean',
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string='Проверка на руководителя ответственного',
            type='boolean',
            invisible=True
        ),

        'check_e': fields.function(
            _check_access,
            method=True,
            string='Проверка на равенство автора и руководителя',
            type='boolean',
            invisible=True
        ),

        'check_x': fields.function(
            _check_access,
            method=True,
            string='Проверка на наличие руководителя в родительской',
            type='boolean',
            invisible=True
        ),

        'color': fields.function(
            _check_color,
            method=True,
            string='Цвет',
            type='char',
            size=20,
            invisible=True
        ),

        'transfer_id': fields.many2one(
            'kpi.smart',
            string='Перенесенная задача',
            readonly=True,
            help='Ссылка на перенесенную задачу'),
        'parent_id': fields.many2one(
            'kpi.smart',
            string='Родительская задача',
            readonly=True,
            help='Ссылка на задачу, из которой была создана текущая задача'),
        'parent_responsible_id': fields.related(
            'parent_id',
            'responsible_id',
            type='many2one',
            relation='hr.employee',
            string='Ответственный в родительской задаче',
            help=''
        ),
        'delegate_ids': fields.one2many(
            'kpi.smart',
            'parent_id',
            string='Делегированные задачи',
            readonly=True,
            help='Список подзадач, созданных путем делегирования.'),
        'kpi_id': fields.many2one(
            'kpi.kpi',
            string='KPI',
            readonly=True,
            help=''),
        'nbr': fields.function(
            _show_number,
            method=True,
            string='Номер',
            type='integer',
            store=False,
            help=''),
    }

    _defaults = {
        'author_id': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).id,
        'state': 'draft',
        'calendar': 'rus',
        'check_a': lambda s, c, u, cnt: cnt.get('check_a') or True,
        'kpi_id': lambda s, c, u, cnt: cnt.get('kpi_id')
    }

    def get_state(self, state):
        return [item for item in self._states if item[0] == state][0]

    def onchange_calendar(self, cr, uid, ids, calendar, period_id, context=None):
        period_pool = self.pool.get('kpi.period')
        value = {}
        if period_id:
            period = period_pool.browse(cr, uid, period_id, context)
            if period.calendar != calendar:
                period_ids = period_pool.search(cr, uid, [('name', '=', period.name), ('calendar', '=', calendar)])
                if period_ids:
                    value = {'period_id': period_ids[0]}
        return {'value': value}

    def onchange_deadline(self, cr, uid, ids, deadline, calendar, context=None):
        period = deadline[:7].replace('-', '/')
        period_pool = self.pool.get('kpi.period')
        value = {}
        if period:
            period_ids = period_pool.search(cr, uid, [('name', '=', period), ('calendar', '=', calendar)])
            if period_ids:
                value = {'period_id': period_ids[0]}
        return {'value': value}

    def onchange_responsible(self, cr, uid, ids, responsible_id, author_id, context=None):
        employee_pool = self.pool.get('hr.employee')
        value = {}
        if responsible_id:
            #head = employee_pool.get_department_manager(cr, uid, responsible_id, context)
            employee = employee_pool.browse(cr, uid, responsible_id, context)
            calendar = employee.department_id.department_time
            head = employee.parent_id
            if employee.user_id.id == uid:
                value.update({'check_r': True})
            else:
                value.update({'check_r': False})

            if head:
                if head.user_id.id == uid:
                    value.update({'check_m': True})
                else:
                    value.update({'check_m': False})

                if head.id == author_id:
                    value.update({'check_e': True})
                else:
                    value.update({'check_e': False})
                value.update({'responsible_head_id': head.id, 'calendar': calendar})
        return {'value': value}

    def create(self, cr, uid, values, context=None):
        if context is None:
            context = {}
        employee_pool = self.pool.get('hr.employee')
        kpi_pool = self.pool.get('kpi.kpi')
        calendar = values.get('calendar') or 'rus'

        period_id = values.get('period_id', False)

        if not values.get('responsible_id', False) and values.get('kpi_id', False):
            kpi = self.pool.get('kpi.kpi').browse(cr, uid, values['kpi_id'])
            values['responsible_id'] = kpi.employee_id.id

        responsible_id = values.get('responsible_id', False)
        initiator_id = values.get('initiator_id', False)
        deadline_date = values.get('deadline_date', False)

        if not initiator_id:
            values.update({'initiator_id': self.pool.get('hr.employee').get_employee(cr, uid, uid).id})

        if responsible_id:
            employee = employee_pool.browse(cr, uid, values['responsible_id'], context)
            calendar = employee.department_id.department_time
            head = employee.parent_id
            if head:
                values.update({'responsible_head_id': head.id, 'calendar': calendar})

        if not period_id and deadline_date:
            period = self.pool.get('kpi.period').get_by_date(
                cr,
                datetime.strptime(deadline_date, "%Y-%m-%d %H:%M:%S"),
                calendar)

            period_id = period.id

        if period_id and responsible_id:
            kpi_ids = kpi_pool.search(cr, 1, [('period_id', '=', period_id), ('employee_id', '=', responsible_id)])
            if kpi_ids:
                values.update({'kpi_id': kpi_ids[0]})
                self._create_kpi_mbo_smart(cr, uid, kpi_ids[0])
            else:
                if values.get('kpi_id'):
                    del values['kpi_id']

        if values.get('deadline_date', False):
            values.update(self.onchange_deadline(cr, uid, [], values['deadline_date'], calendar, context)['value'])

        return super(KpiSmart, self).create(cr, uid, values, context)

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        _logger.info("SMART write")
        if context is None:
            context = {}

        employee_pool = self.pool.get('hr.employee')
        kpi_pool = self.pool.get('kpi.kpi')

        record = self.browse(cr, 1, ids, context)[0]
        next_state = values.get('state', False)
        state = record.state

        initiator = values.get('initiator_id') or record.initiator_id.id

        mbo_pool = self.pool.get('kpi.mbo')
        smart_mbo_id = self.pool.get('kpi.indicators.reference').search(cr, uid, [('name', 'ilike', 'SMART')])

        smart_fact = 0
        smart_plan = 0
        mbo_ids = mbo_pool.search(cr, 1, [('name.id', '=', smart_mbo_id[0]), ('kpi_id.id', '=', record.kpi_id.id)])

        if record.kpi_id:
            smart_fact = self._get_fact(cr, record.kpi_id.period_id.id, record.kpi_id.employee_id.id)
            smart_plan = self._get_plan(cr, record.kpi_id.period_id.id, record.kpi_id.employee_id.id)
        else:
            kpi_ids = kpi_pool.search(cr, 1, [('period_id', '=', record.period_id.id), ('employee_id', '=', record.responsible_id.id)])
            if kpi_ids:
                values['kpi_id'] = kpi_ids[0]
                smart_fact = self._get_fact(cr, record.period_id.id, record.responsible_id.id)
                smart_plan = self._get_plan(cr, record.period_id.id, record.responsible_id.id)

        if not initiator:
            values['initiator_id'] = values.get('author_id') or record.author_id.id

        calendar = values.get('calendar') or record.calendar
        responsible = 0
        if values.get('responsible_id', False):
            responsible = values.get('responsible_id', False)
        else:
            if values.get('kpi_id', False):
                kpi = self.pool.get('kpi.kpi').browse(cr, uid, values['kpi_id'])
                responsible = kpi.employee_id.id
                values['responsible_id'] = responsible

        if responsible:
            employee = employee_pool.browse(cr, 1, responsible, context)
            calendar = employee.department_id.department_time
            head = employee.parent_id
            if head:
                values.update({'responsible_head_id': head.id, 'calendar': calendar})

        if values.get('deadline_date', False):
            if not self._check_access(cr, uid, ids, 'check_r', {}, context):
                values.update({'deadline_check': True})
            values.update(self.onchange_deadline(cr, uid, ids, values['deadline_date'], calendar, context)['value'])

        if next_state and next_state != state:
            values.update({'history_ids': [(0, 0, {
                'usr_id': self.pool.get('hr.employee').get_employee(cr, 1, uid).id,
                'state': self.get_state(next_state)[1]
            })]})
            if next_state == 'accepted':
                smart_fact += 1
            if next_state == 'inwork':
                if smart_plan < 10:
                    smart_plan += 1

        if mbo_ids:
            mbo_pool.write(cr, uid, mbo_ids[0], {'fact': smart_fact, 'plan': smart_plan})

        if record.kpi_id:
            smart_ids = self.search(cr, uid, [
                ('responsible_id', '=', responsible),
                ('period_id', '=', record.kpi_id.period_id.id),
                ('kpi_id', '=', False)
            ])
            if smart_ids:
                self.write(cr, uid, smart_ids, {'kpi_id': record.kpi_id.id})
            mbo = kpi_pool._calculate_total_mbo(cr, 1, [record.kpi_id.id], 'total_mbo', [], context)[record.kpi_id.id]
            if mbo != record.kpi_id.total_mbo:
                kpi_pool.write(cr, 1, [record.kpi_id.id], {'total_mbo': mbo})

        return super(KpiSmart, self).write(cr, uid, ids, values, context)

    def copy(self, cr, uid, id, values=None, context=None):
        values['responsible_id'] = None
        values['responsible_head_id'] = None
        values['history_ids'] = None
        values['state'] = 'draft'
        return super(KpiSmart, self).copy(cr, uid, id, values, context)

    def unlink(self, cr, uid, ids, context=None):
        kpi = self.browse(cr, uid, ids[0]).kpi_id
        super(KpiSmart, self).unlink(cr, uid, ids, context)
        if kpi:
            smart_fact = self._get_fact(cr, kpi.period_id.id, kpi.employee_id.id) or 0
            smart_plan = self._get_plan(cr, kpi.period_id.id, kpi.employee_id.id) or 0
            mbo_pool = self.pool.get('kpi.mbo')
            smart_mbo_id = self.pool.get('kpi.indicators.reference').search(cr, uid, [('name', 'ilike', 'SMART')])
            if smart_mbo_id:
                mbo_ids = mbo_pool.search(cr, 1, [('name.id', '=', smart_mbo_id[0]), ('kpi_id.id', '=', kpi.id)])
                if mbo_ids:
                    mbo_pool.write(cr, uid, mbo_ids[0], {'fact': smart_fact, 'plan': smart_plan})
        return True

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        period_pool = self.pool.get('kpi.period')
        period = [item for item in args if item[0] == 'period_id']

        if period:
            if isinstance(period[0][2], (tuple, list)):
                period_id = period[0][2][0]
            else:
                period_id = period[0][2]
            period_name = period_pool.browse(cr, user, period_id)

            domain = [('name', '=', period_name.name)]

            need_period_ids = period_pool.search(cr, user, domain)
            if need_period_ids:
                args.remove(period[0])
                args.append(('period_id', 'in', need_period_ids))
        return super(KpiSmart, self).search(cr, user, args, offset, limit, order, context, count)

    def action_transfer(self, cr, uid, ids, type="transfer", context=None):
        fields = ['name', 'note', 'author_id', 'initiator_id', 'responsible_id', 'responsible_head_id', 'calendar',
                  'deadline_date']
        for record in self.read(cr, uid, ids, fields, context):
            record['parent_id'] = record['id']
            if type == "delegated":
                record['author_id'] = record['responsible_id']
                record['initiator_id'] = record['responsible_id']
                record['deadline_date'] = record['deadline_date']

                record['responsible_id'] = None
                record['responsible_head_id'] = None
            if type == "transfer":
                new_date = datetime.strptime(record['deadline_date'], "%Y-%m-%d %H:%M:%S") + \
                                          relativedelta(months=+1)

                record['deadline_date'] = new_date.strftime("%Y-%m-%d %H:%M:%S")

            del record['id']
            for key in record:
                if 'id' in key and isinstance(record[key], (tuple, list)):
                    record[key] = record[key][0]

            new_id = self.create(cr, uid, record, context)
            state = 'delegated' if type == "delegated" else 'transfer'
            self.write(cr, uid, ids, {'transfer_id': new_id, 'state': state})

            view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'kpi.smart.form'),
                                                                   ('model', '=', self._name)])
            return {
                'name': "Smart-задача: %s" % ("Делегирована" if type == "delegated" else "Перенесена"),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': self._name,
                'views': [(view_id[0], 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'check_a': True},
                'res_id': new_id,
            }

    def delegate(self, cr, uid, ids, context=None):
        return self.action_transfer(cr, uid, ids, 'delegated', context)

    def _check_deadline(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids):
            now = datetime.now() + timedelta(days=1)
            if record.deadline_date:
                deadline = datetime.strptime(record.deadline_date, "%Y-%m-%d %H:%M:%S")
                if not self._check_access(cr, uid, ids, 'check_r', {},
                                          context) and record.deadline_check and now > deadline:
                    return False
        return True

    _constraints = [
        (_check_deadline,
         'Нельзя изменять дату выполнения более 1 раза или меньше чем за сутки до выполнения.',
         [u'Срок выполнения']),
    ]
KpiSmart()


class KpiSmartHistory(Model):
    _name = 'kpi.smart.history'
    _description = u'KPI - SMART: История переходов'
    _log_create = True
    _order = "create_date desc"
    _rec_name = 'state'

    _columns = {
        'usr_id': fields.many2one('hr.employee', u'Перевел'),
        'state': fields.char(u'На этап', size=65),
        'create_date': fields.datetime(u'Дата', readonly=True),
        'smart_id': fields.many2one('kpi.smart', 'Smart', invisible=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: self.pool.get('hr.employee').get_employee(cr, uid, uid).id,
    }
KpiSmartHistory()


class Kpi(Model):
    _name = 'kpi.kpi'
    _description = u'KPI'
    _order = 'period_name DESC'

    def _get_name(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = u"KPI сотрудника %s за %s" % (record.employee_id.name, record.period_id.name)
        return res

    def _get_grade(self, cr, uid, period_id, employee_id, context=None):
        grade_history_pool = self.pool.get('kpi.grade.history')
        period_pool = self.pool.get('kpi.period')
        period = period_pool.browse(cr, uid, period_id)

        history_ids = grade_history_pool.search(cr, 1, [('employee_id', '=', employee_id), ('period_id.name', '<=', period.name)])
        if history_ids:
            history_obj = grade_history_pool.read(cr, 1, history_ids[0], ['next_grade_id', 'next_dy_cash'])
            grade_id = history_obj['next_grade_id'][0]
            if grade_id == 46:
                cash = history_obj['next_dy_cash']
            else:
                grade_dict = self.pool.get('kpi.grade').read(cr, 1, grade_id, ['cash'])
                cash = grade_dict['cash']
            return history_obj['next_grade_id'][1], cash
        return None, 0.0

    def _get_days(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            days = self._calculate_days(
                cr, uid,
                record.period_id.id,
                record.employee_id.id,
                record.fact_days
            )
            res[record.id] = days
        return res

    def _get_holidays(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            days = self._calculate_holidays(
                cr, uid,
                record.period_id.id,
                record.employee_id.id
            )
            res[record.id] = days
        return res

    def _get_cash(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['grade_cash', 'sv', 'days', 'work_days_1', 'total_mbo', 'without_mbo', 'night_work', 'cash_night', 'weekend_work', 'cash_weekend'], context):
            salary, variable, total = self._calculate_cash(
                record['grade_cash'],
                record['sv'],
                record['days'],
                record['work_days_1'] or 1,
                record['total_mbo'],
                record['without_mbo'],
                record['night_work'],
                record['cash_night'],
                record['weekend_work'],
                record['cash_weekend']
            )
            res[record['id']] = {
                'salary': salary,
                'variable': variable,
                'total': total
            }
        return res

    def _get_employee_items(self, cr, uid, ids, name, arg, context=None):
        res = {}
        ef = self.pool.get('kpi.enrollment.formal')
        tax_pool = self.pool.get('kpi.formal.tax')
        advance_pool = self.pool.get('kpi.advance')
        retention_pool = self.pool.get('kpi.retention')
        award_pool = self.pool.get('kpi.award')
        for record in self.browse(cr, uid, ids, context):
            item = 0.0

            domain = [('employee_id', '=', record.employee_id.id), ('period_id', '=', record.period_id.id)]

            if name == 'formal_cash':
                pool = ef
            elif name == 'formal_tax':
                pool = tax_pool
            elif name == 'advance':
                pool = advance_pool
            elif name == 'retention':
                pool = retention_pool
            elif name == 'award':
                pool = award_pool

            record_ids = pool.search(cr, uid, domain)
            item = sum([r.cash for r in pool.browse(cr, uid, record_ids)]) or 0.0

            res[record.id] = item
        return res

    def _get_total_pay(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = self._calculate_pay(
                record.total, record.retention, record.advance, record.formal_cash, record.formal_tax, record.award
            )
        return res

    def _get_total_earned(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = self._calculate_earned(
                record.total, record.retention, record.advance, record.formal_cash, record.formal_tax, record.award
            )
        return res

    def _get_default_period(self, cr, uid):
        period_pool = self.pool.get('kpi.period')
        employee = self.pool.get('hr.employee').get_employee(cr, uid, uid)
        kpi_ids = self.search(cr, uid, [('employee_id.id', '=', employee.id)])

        if kpi_ids:
            kpi = self.browse(cr, uid, kpi_ids[0])
            next_period = period_pool.next(cr, kpi.period_id.id)
            period_id = next_period.id
        else:
            period = period_pool.get_by_date(cr, date.today(), employee.department_id.department_time or 'rus')
            period_id = period.id
        return period_id

    def _get_default_grade(self, cr, uid):
        grade_history_pool = self.pool.get('kpi.grade.history')
        employee = self.pool.get('hr.employee').get_employee(cr, uid, uid)
        gh_ids = grade_history_pool.search(
            cr,
            uid,
            [('employee_id.id', '=', employee.id), ('period_id.name', '>', record.period_id.name)]
        )
        hg = grade_history_pool.browse(cr, uid, gh_ids)
        return {'name': 'D1', 'cash': 100.00}

    def _get_default_sv(self, cr, uid):
        employee = self.pool.get('hr.employee').get_employee(cr, uid, uid)
        kpi_ids = self.search(cr, uid, [('employee_id.id', '=', employee.id)], limit=1)
        if kpi_ids:
            kpi = self.read(cr, uid, kpi_ids[0], ['sv'])
            return kpi['sv']

    def _get_default_schedule(self, cr, uid):
        employee = self.pool.get('hr.employee').get_employee(cr, uid, uid)
        kpi_ids = self.search(cr, uid, [('employee_id.id', '=', employee.id)], limit=1)
        if kpi_ids:
            kpi = self.browse(cr, uid, kpi_ids[0])
            return kpi.schedule

    def _get_fact(self, cr, user, pool, fact, id, next_kpi_id):
        item = pool.browse(cr, user, id)
        next_kpi = pool.search(cr, user, [('name.id', '=', item.name.id), ('kpi_id', '=', next_kpi_id)])
        if next_kpi:
            return 1, next_kpi[0], {'previous_period': fact}
        return 1, 0, {'previous_period': fact}

    def _get_formalized(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = record.employee_id.formalized
        return res

    def _get_grade_f(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            grade, grade_cash = self._get_grade(cr, uid, record.period_id.id, record.employee_id.id, context)
            res[record.id] = {'grade': grade, 'grade_cash': grade_cash}
        return res

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.browse(cr, uid, ids, context):
            access = str()

            group_work = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'HR / KPI')])
            users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_work)], order='id')
            if uid in users_work:
                access += 'r'

            if data.employee_id and data.employee_id.user_id.id == uid:
                access += 'e'

            if data.employee_id and not data.employee_id.active and data.parent_id and data.parent_id.user_id.id == uid:
                access += 'e'

            if data.parent_id and data.parent_id.user_id.id == uid:
                access += 'h'

            val = False
            letter = name[6]

            if letter in access or uid == 1:
                val = True
            res[data.id] = val
        return res

    def _calculate_total_mbo(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            if not record.without_mbo:
                res[record.id] = sum(mbo.mbo for mbo in record.mbo_ids)
            else:
                res[record.id] = 100
        return res

    def _calculate_cash(self, grade_cash=0.0, sv='60-40', days=0, work_days=1, total_mbo=100,
                        without_mbo=False, night_work=0, cash_night=0.0, weekend_work=0, cash_weekend=0.0):
        salary_factor = .0
        variable_factor = .0
        total = 0

        if sv == '60-40':
            salary_factor = .6
            variable_factor = .4
        elif sv == '20-80':
            salary_factor = .2
            variable_factor = .8
        elif sv == '40-60':
            salary_factor = .4
            variable_factor = .6

        mbo = total_mbo / 100
        if without_mbo:
            salary_factor = 1
            variable_factor = 0

        salary = grade_cash * salary_factor
        variable = grade_cash * variable_factor
        day_factor = days / work_days

        total = salary * day_factor + variable * mbo + night_work * cash_night + weekend_work * cash_weekend

        return salary, variable, total

    def _calculate_pay(self, cash=0.0, retention=0.0, advance=0.0, formal_cash=0.0, formal_tax=0.0, award=0.0):
        return cash + award - retention - advance - formal_cash - formal_tax

    def _calculate_days(self, cr, uid, period_id, employee_id, fact_days=0):
        days = self._calculate_holidays(cr, uid, period_id, employee_id)
        return fact_days + days

    def _calculate_holidays(self, cr, uid, period_id, employee_id):
        holidays_pool = self.pool.get('hr.holidays')
        period = self.pool.get('kpi.period').browse(cr, uid, period_id)
        start_month = period.month
        start_year = period.year

        period_date = date(int(start_year), int(start_month), 3)
        end_month, end_year = add_months(period_date, 1)
        if start_month < 10:
            start_month = "0%s" % start_month
        if end_month < 10:
            end_month = "0%s" % end_month

        start_period = "%s-%s-03" % (start_year, start_month)
        end_period = "%s-%s-03" % (end_year, end_month)

        holidays_ids = holidays_pool.search(
            cr,
            uid,
            [
                ('employee_id', '=', employee_id),
                ('holiday_status_id', 'in', (17, 22, 24, 25)),
                ('date_to', '>=', start_period),
                ('date_to', '<=', end_period),
                ('state', '=', 'confirm')
            ])
        days = 0
        for record in holidays_pool.browse(cr, uid, holidays_ids):
            if record.date_from < start_period:
                date_from = start_period
            else:
                date_from = record.date_from
            date_from = datetime.strptime(date_from[:10], "%Y-%m-%d")

            if record.date_to > end_period:
                date_to = end_period
            else:
                date_to = record.date_to
            date_to = datetime.strptime(date_to[:10], "%Y-%m-%d")
            delta = date_to - date_from
            days += delta.days + 1
        return days

    def change_period(self, cr, uid, ids, employee_id, period_id, calendar, context=None):
        period_pool = self.pool.get('kpi.period')
        smart_pool = self.pool.get('kpi.smart')
        value = {}

        if self.search(cr, uid, [('employee_id.id', '=', employee_id), ('id', 'not in', ids),
                                 ('period_id.id', '=', period_id), ('calendar', '=', calendar)]):
            raise osv.except_osv("Error", "Вы не можете создать более 1го KPI на определененый месяц!")
        else:
            period = period_pool.browse(cr, uid, period_id, context)
            value['work_days_1'] = period.days
            kpi_ids = self.search(
                cr,
                uid,
                [
                    ('employee_id.id', '=', employee_id),
                    ('period_id.name', '<', period.name)
                ]
            )
            mbo = []
            sla = []
            sale = []
            experts = []
            ink_employment = 0
            upsale_employment = 0
            grade_cash_kpi = 0
            if kpi_ids:
                prev_kpi = self.browse(cr, uid, kpi_ids[0])

                mbo = [(0, 0, {'name': i.name.id, 'units': i.units, 'weight': i.weight, 'previous_period': i.fact})
                       for i in prev_kpi.mbo_ids]
                sla = [(0, 0, {'name': i.name.id, 'units': i.units, 'weight': i.weight, 'previous_period': i.fact})
                       for i in prev_kpi.sla_ids]
                sale = [(0, 0, {'name': i.name.id, 'units': i.units, 'weight': i.weight})
                        for i in prev_kpi.sla_sale_ids]
                experts = [(6, 0, [r.id for r in prev_kpi.experts_ids])]

                grade_cash_kpi = prev_kpi.grade_cash

                ink_employment = prev_kpi.ink_employment
                upsale_employment = prev_kpi.upsale_employment

            else:
                kpi_ids = self.search(cr, uid, [('employee_id.id', '=', employee_id)])
                if kpi_ids:
                    record = self.browse(cr, uid, kpi_ids[0])

                    mbo = [(0, 0, {'name': i.name.id, 'units': i.units, 'weight': i.weight, 'previous_period': 0.0})
                           for i in record.mbo_ids]
                    sla = [(0, 0, {'name': i.name.id, 'units': i.units, 'weight': i.weight, 'previous_period': 0.0})
                           for i in record.sla_ids]
                    sale = [(0, 0, {'name': i.name.id, 'units': i.units, 'weight': i.weight})
                            for i in record.sla_sale_ids]
                    experts = [(6, 0, [r.id for r in record.experts_ids])]

                    ink_employment = record.ink_employment
                    upsale_employment = record.upsale_employment

                    grade_cash_kpi = record.grade_cash

            if mbo:
                value.update({'mbo_ids': mbo})
            if sla:
                value.update({'sla_ids': sla})
            if sale:
                value.update({'sla_sale_ids': sale})
            if experts:
                value.update({'experts_ids': experts})

            grade, grade_cash = self._get_grade(cr, uid, period.id, employee_id, context)
            if grade:
                value.update({'grade': grade, 'grade_cash': grade_cash})
            elif grade_cash_kpi:
                value.update({'grade_cash': grade_cash_kpi})

            smart_ids = smart_pool.search(cr, uid, [
                ('period_id.id', '=', period_id), ('responsible_id.id', '=', employee_id)
            ])
            if smart_ids:
                value.update({'smart_ids': [(4, s) for s in smart_ids]})

            value.update(
                {
                    'holidays': self._calculate_holidays(cr, uid, period_id, employee_id),
                    'ink_employment': ink_employment,
                    'upsale_employment': upsale_employment
                })
        return {'value': value}

    def change_days(self, cr, uid, ids, period_id, employee_id, fact_days=0, context=None):
        days = self._calculate_days(cr, uid, period_id, employee_id, fact_days)
        return {'value': {'days': days}}

    def change_calendar(self, cr, uid, ids, calendar, period_id, context=None):
        period_pool = self.pool.get('kpi.period')
        value = {}
        if period_id:
            period = period_pool.browse(cr, uid, period_id, context)
            if period.calendar != calendar:
                period_ids = period_pool.search(cr, uid, [('name', '=', period.name), ('calendar', '=', calendar)])
                if period_ids:
                    value = {'period_id': period_ids[0]}
                else:
                    value = {'period_id': None}
        return {'value': value}

    def change_mbo(self, cr, uid, ids, without_mbo, context=None):
        mbo = 100
        if not without_mbo:
            mbo = self._calculate_total_mbo(cr, uid, ids, 'total_mbo', [], context)[ids[0]]

        return {'value': {'total_mbo': mbo}}

    def change_mbo_ids(self, cr, uid, ids, context=None):
        mbo = self._calculate_total_mbo(cr, uid, ids, 'total_mbo', [], context)[ids[0]]
        return {'value': {'total_mbo': mbo}}

    def change_cash(self, cr, uid, ids, grade_cash=0.0, sv='60-40', days=0, work_days=1, total_mbo=100,
                    without_mbo=False, night_work=0, cash_night=0.0, weekend_work=0, cash_weekend=0.0, context=None):
        salary, variable, total = self._calculate_cash(
            grade_cash,
            sv,
            days,
            work_days or 1,
            total_mbo,
            without_mbo,
            night_work,
            cash_night,
            weekend_work,
            cash_weekend
        )
        return {
            'value': {
                'salary': salary,
                'variable': variable,
                'total': total,
            }
        }

    def change_pay(self, cr, uid, ids, cash=0.0, retention=0.0, advance=0.0, formal_cash=0.0, formal_tax=0.0,
                   award=0.0):
        pay = self._calculate_pay(cash, retention, advance, formal_cash, formal_tax, award)
        return {'value': {'total_pay': pay}}

    def expert_operations(self, cr, uid, ids, future_experts):
        """
            Метод необходим для автоматизации управления
            черновиками эспертных оценок.
            При изменении поля @experts - с объектом kpi.experts.assesment будут
            происходить соответствующие изменения
            @future_experts - список экспертов, которые будут добавлены

            В методе происходит работа с множествами и на основе разницы
            в новых и текущих экспертах происходит соответственно удаление
            или создание объектов kpi.expert.assesment
        """
        data = self.read(cr, uid, ids[0], ['employee_id', 'experts_ids', 'period_id'])

        new_experts = list(set(future_experts) - set(data['experts_ids']))
        del_experts = list(set(data['experts_ids']) - set(future_experts))
        expert_pool = self.pool.get('kpi.expert.assesment')
        for expert in new_experts:
            expert_pool.create(cr, 1, {
                'kpi_id': data['id'],
                'employee_id': data['employee_id'][0],
                'expert_id': expert,
                'period_id': data['period_id'][0]
            })
        if del_experts:
            del_expert_assesments = expert_pool.search(
                cr,
                uid,
                [
                    ('kpi_id', '=', data['id']),
                    ('expert_id', 'in', del_experts)
                ])
            expert_pool.unlink(cr, uid, del_expert_assesments)

        return True

    def _calculate_mean(self, cr, uid, ids, name, arg, context=None):
        """
            Расчет средней оценки.
            Если показатели не самоотвод:
                Суммируем и делим на их количество.
                Округляем до двух знаков после запятой.
        """
        result = {}

        def compute_value(*args):
            if u'самоотвод' in args:
                return False
            else:
                return round(numpy.mean([map(float, args)]), 2)

        data = self.browse(cr, uid, ids, context)
        for row in data:
            result[row.id] = compute_value(row.client, row.standards, row.quality)
        return result

    _states = (
        ('draft', 'Черновик'),
        ('waiting', 'Требуется утверждение планов руководителем'),
        ('waiting_revision', 'На доработке (требуется утверждение планов)'),
        ('planned', 'Планы на месяц утверждены'),
        ('planned_revision', 'На доработке (планы утверждены)'),
        ('passed', 'KPI сдан руководителю'),
        ('passed_revision', 'На доработке (сдан руководителю)'),
        ('agreed', 'KPI утвержден руководителем'),
        ('agreed_revision', 'На доработке (утверждены руководителем)'),
        ('saved', 'Сохранен для зарплатной ведомости'),
    )

    def get_grade(self, cr, date, employee_id):
        period = self.get_period(cr, date, employee_id)
        history_ids = self.search(cr, 1, [('employee_id', '=', employee_id), ('period_id.name', '<=', period.name)], order='create_date desc')
        if history_ids:
            history_obj = self.read(cr, 1, history_ids[0], ['next_grade_id', 'next_dy_cash'])
            return history_obj['next_grade_id'][0], history_obj['next_dy_cash']
        return None, 0.0

    _columns = {
        'name': fields.function(
            _get_name,
            method=True,
            string="Название",
            type="char",
            size=250),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', readonly=True),
        'company_id': fields.related(
            'employee_id',
            'company_id',
            relation='res.company',
            type='many2one',
            store=False
        ),
        'formalized': fields.function(
            _get_formalized,
            type='boolean',
            string='Официально устроен',
            method=True),
        'parent_id': fields.many2one('hr.employee', 'Руководитель', readonly=True),
        'job_id': fields.many2one('hr.job', 'Должность', readonly=True),

        'state': fields.selection(_states, 'Статус', readonly=True),
        'history_ids': fields.one2many('kpi.history', 'kpi_id', 'История переходов'),

        'period_id': fields.many2one('kpi.period', 'Период'),
        'period_name': fields.related(
            'period_id',
            'name',
            type='char',
            size=7,
            store=True
        ),
        'calendar': fields.selection(
            [
                ('ua', 'Украина'),
                ('rus', 'Россия'),
                ('eu', 'ЕС')
            ], 'Рабочее время', readonly=True, select=True),

        'salary': fields.function(
            _get_cash,
            type='float',
            string='Окладная часть',
            store=False,
            multi='all'),
        'variable': fields.function(
            _get_cash,
            type='float',
            string='Переменная часть',
            store=False,
            multi='all'),
        'total': fields.function(
            _get_cash,
            type='float',
            string='Совокупный доход',
            store=False,
            multi='all'),

        'attachment_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Загружаемые файлы',
            domain=[('res_model', '=', 'kpi.kpi')],
            context={'res_model': 'kpi.kpi'}
        ),
        'comment': fields.text('Комментарий по доработке'),

        #  Smart-задачи
        'smart_ids': fields.one2many(
            'kpi.smart',
            'kpi_id',
            'SMART-задачи'
        ),
        #  Ключевые показатели
        'total_mbo': fields.function(
            _calculate_total_mbo,
            method=True,
            string='Итого MBO',
            type='float',
            store=True),
        'mbo_ids': fields.one2many('kpi.mbo', 'kpi_id', 'MBO'),
        'without_mbo': fields.boolean('Без учета MBO'),

        #  ЭО
        'experts_ids': fields.many2many(
            'hr.employee',
            'kpi_experts_rel',
            'kpi_id',
            'expert_id',
            'Эксперты',
            ondelete='cascade'
        ),
        'expert_assesments': fields.one2many(
            'kpi.expert.assesment',
            'kpi_id',
            'Экспертные оценки',
            domain=[('state', '=', 'work')]
        ),

        # Work days
        'work_days_1': fields.related('period_id', 'days', type="integer", string='Рабочие дни в отчетном периоде',
                                      store=True),
        'schedule': fields.selection(
            (
                ('8-17', '8-17'),
                ('9-18', '9-18'),
                ('10-19', '10-19'),
                ('float', 'Плавающий'),
            ), 'График работы'),
        'night_work': fields.integer('Работа в ночные смены'),
        'weekend_work': fields.integer('Работа в выходные смены'),
        'fact_days': fields.integer('Фактически отработанные дни'),
        'holidays': fields.function(
            _get_holidays,
            type='integer',
            string='Количество дней в отпусках'
        ),
        'days': fields.function(
            _get_days,
            type='integer',
            string='Количество отработанных дней для расчета ЗП'
        ),

        #  Партнеры
        'partners_prev': fields.integer('Количество партнеров в предыдущем периоде'),
        'partners': fields.integer('Количество партнеров в отчетном периоде'),
        'partners_canceled': fields.integer('Количество отказавшихся партнеров'),

        #  SLA
        'sla_ids': fields.one2many('kpi.sla', 'kpi_id', 'SLA'),

        #  SLA - 2
        'sla2_ids': fields.one2many('kpi.sla2', 'kpi_id', 'SLA - 2'),

        #  SLA sale
        'sla_sale_ids': fields.one2many('kpi.sla.sale', 'kpi_id', 'SLA'),

        #  Расчет
        'upsale_employment': fields.integer('Занятость в UpSale'),
        'ink_employment': fields.integer('Занятость в INKSYSTEM'),

        'grade': fields.function(
            _get_grade_f,
            type='char',
            size=50,
            string='Грейд',
            store=False,
            multi='grade'),
        'grade_cash': fields.function(
            _get_grade_f,
            type='float',
            digits=(6, 2),
            string='Сумма начисления по грейду',
            store=False,
            multi='grade'),
        #'grade_cash': fields.float('Сумма начисления по грейду', digits=(6, 2),),
        'cash_night': fields.float('Работа в ночную смену', digits=(6, 2), help='Стоимость 1 дня'),
        'cash_weekend': fields.float('Работа в выходные', digits=(6, 2), help='Стоимость 1 дня'),
        'sv': fields.selection(
            (
                ('60-40', '60/40'),
                ('20-80', '20/80'),
                ('40-60', '40/60'),
            ), 'Разбивка окладной и переменной частей'
        ),

        'formal_cash': fields.function(
            _get_employee_items,
            type='float',
            string='Официальная ЗП',
            method=True),
        'formal_tax': fields.function(
            _get_employee_items,
            type='float',
            string='Налог с официальной ЗП',
            method=True),
        'advance': fields.function(
            _get_employee_items,
            type='float',
            string='Аванс',
            method=True),
        'retention': fields.function(
            _get_employee_items,
            type='float',
            string='Удержание',
            method=True),
        'award': fields.function(
            _get_employee_items,
            type='float',
            string='Премия',
            method=True),

        'total_pay': fields.function(
            _get_total_pay,
            type='float',
            string='Сумма начисления'
        ),
        #'total_earned': fields.function(
        #    _get_total_earned,
        #    type='float',
        #    string='Общая сумма',
        #    method=True),

        'check_e': fields.function(
            _check_access,
            method=True,
            string='Сотрудник',
            type='boolean',
            invisible=True
        ),
        'check_h': fields.function(
            _check_access,
            method=True,
            string='Руководитель',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='HR',
            type='boolean',
            invisible=True
        ),

        #  Самооценка
        'client': fields.selection(
            [
                ('-2', '-2'),
                ('-1', '-1'),
                ('0', '0'),
                ('1', '+1'),
                ('2', '+2'),
                ('самоотвод', 'самоотвод')
            ], 'Клиентоориентированность, оценка',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'client_note1': fields.text('Примечание 1', states={
            'agreed': [('readonly', True)],
            'agreed_revision': [('readonly', True)],
            'saved': [('readonly', True)],
        }),
        'client_note2': fields.text(
            'Примечание 2',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'client_note3': fields.text(
            'Примечание 3',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'standards': fields.selection(
            [
                ('-2', '-2'),
                ('-1', '-1'),
                ('0', '0'),
                ('1', '+1'),
                ('2', '+2'),
                ('самоотвод', 'самоотвод')
            ], 'Соблюдение стандартов, оценка',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'standards_note1': fields.text(
            'Примечание 1',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'standards_note2': fields.text(
            'Примечание 2',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'standards_note3': fields.text(
            'Примечание 3',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'quality': fields.selection(
            [
                ('-2', '-2'),
                ('-1', '-1'),
                ('0', '0'),
                ('1', '+1'),
                ('2', '+2'),
                ('самоотвод', 'самоотвод')
            ], 'Качество работы, оценка',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'quality_note1': fields.text(
            'Примечание 1',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'quality_note2': fields.text(
            'Примечание 2',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'quality_note3': fields.text(
            'Примечание 3',
            states={
                'agreed': [('readonly', True)],
                'agreed_revision': [('readonly', True)],
                'saved': [('readonly', True)],
            }),
        'mean': fields.function(
            _calculate_mean,
            method=True,
            string="Среднее значение",
            type="float",
            store=True
        ),

    }

    _defaults = {
        'employee_id': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).id,
        'formalized': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).formalized,
        'parent_id': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).parent_id.id,
        'job_id': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).job_id.id,
        'state': 'draft',
        'calendar': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u,
                                                                                u).department_id.department_time or 'rus',
        'check_e': True,
        'schedule': lambda s, c, u, cnt: s._get_default_schedule(c, u) or '9-18',
        'period_id': lambda s, c, u, cnt: s._get_default_period(c, u),
        'sv': lambda s, c, u, cnt: s._get_default_sv(c, u) or '60-40',

    }

    def get_state(self, state):
        return [item for item in self._states if item[0] == state][0]

    def next(self, cr, kpi_id):
        try:
            kpi = self.browse(cr, 1, kpi_id)
            next_period = self.pool.get('kpi.period').next(cr, kpi.period_id.id)
            next_kpi_ids = self.search(cr, 1, [
                ('employee_id.id', '=', kpi.employee_id.id),
                ('period_id.id', '=', next_period.id)])
            result = self.browse(cr, 1, next_kpi_ids[0])
            return result
        except IndexError:
            return browse_null()

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        period = [item for item in args if item[0] == 'period_id']
        employee_time = [item for item in args if item[0] == 'calendar']
        period_pool = self.pool.get('kpi.period')

        if employee_time:
            calendar_type = employee_time[0][2]
        else:
            calendar_type = ''

        if period:
            if isinstance(period[0][2], (tuple, list)):
                period_id = period[0][2][0]
            else:
                period_id = period[0][2]
            period_name = period_pool.browse(cr, uid, period_id)

            domain = [('name', '=', period_name.name)]

            if calendar_type:
                domain.append(('calendar', '=', calendar_type))

            need_period_ids = period_pool.search(cr, uid, domain)
            if need_period_ids:
                args.remove(period[0])
                args.append(('period_id', 'in', need_period_ids))

        return super(Kpi, self).search(cr, uid, args, offset, limit, order, context, count)

    def create(self, cr, user, vals, context=None):
        smart_pool = self.pool.get('kpi.smart')
        expert_pool = self.pool.get('kpi.expert.assesment')
        period_pool = self.pool.get('kpi.period')

        employee_id = vals.get('employee_id', False) or self.pool.get('hr.employee').get_employee(cr, user, user).id
        period_id = vals.get('period_id', False)
        period = period_pool.read(cr, user, period_id, ['calendar'])
        experts = []
        if period:
            prev_value = self.change_period(cr, user, [], employee_id, period_id, period['calendar'], context)
            if prev_value['value'].get('experts_ids'):
                experts = prev_value['value']['experts_ids']
                vals['experts_ids'] = experts

        kpi_id = super(Kpi, self).create(cr, user, vals, context)
        if employee_id and period_id:
            smart_ids = smart_pool.search(cr, user,
                                          [('responsible_id.id', '=', employee_id), ('period_id', '=', period_id)])
            if smart_ids:
                smart_pool.write(cr, user, smart_ids, {'kpi_id': kpi_id})

            if experts:
                for expert in experts:
                    if expert[2]:
                        for ex in expert[2]:
                            expert_pool.create(cr, 1, {
                                'kpi_id': kpi_id,
                                'employee_id': employee_id,
                                'expert_id': ex,
                                'period_id': period_id
                            })

        return kpi_id

    @notify.msg_send(_name)
    def write(self, cr, user, ids, vals, context=None):
        _logger.info("KPI write")
        mbo_pool = self.pool.get('kpi.mbo')
        sla_pool = self.pool.get('kpi.sla')
        employee_pool = self.pool.get('hr.employee')

        record = self.browse(cr, 1, ids, context)[0]
        next_state = vals.get('state', False)
        state = record.state

        mbo_ids = vals.get('mbo_ids', [])
        sla_ids = vals.get('sla_ids', [])
        partners = vals.get('partners', 0)

        if vals.get('grade'):
            grade = vals['grade']
        elif record.grade:
            #grade = record.grade.id
            grade = 0
        else:
            grade = 0

        if vals.get('experts_ids'):
            self.expert_operations(cr, user, ids, vals.get('experts_ids')[0][2])

        if vals.get('grade_cash') and (grade == 46 or not grade):
            del vals['grade_cash']

        if mbo_ids or sla_ids or partners and isinstance(ids, (list, tuple)):
            for kpi_id in ids:
                next_kpi = self.next(cr, kpi_id)
                values = {}

                if next_kpi:
                    mbo_facts = [self._get_fact(cr, user, mbo_pool, r[2]['fact'], r[1], next_kpi.id)
                                 for r in mbo_ids if r[2] and r[2].get('fact')]
                    sla_facts = [self._get_fact(cr, user, sla_pool, r[2]['fact'], r[1], next_kpi.id)
                                 for r in sla_ids if r[2] and r[2].get('fact')]
                    mbo_facts = [item for item in mbo_facts if item[1]]
                    sla_facts = [item for item in sla_facts if item[1]]
                    if mbo_facts:
                        values['mbo_ids'] = mbo_facts
                    if sla_facts:
                        values['sla_ids'] = sla_facts
                    if partners:
                        values['partners_prev'] = partners
                    self.write(cr, user, [next_kpi.id], values)

        if next_state and next_state != state:
            if next_state == 'agreed':
                smart_ids = self.pool.get('kpi.smart').search(cr, user, [('kpi_id', '=', record.id), ('state', 'in', ('removed', 'transfer', 'cancel', 'accepterd', 'not_accepted'))])
                if record.smart_ids and smart_ids:
                    _logger.info("SMART count: %s", len(smart_ids))
                    #raise osv.except_osv('KPI', 'Надо закрыть все SMART-задачи.')

            vals.update({'history_ids': [(0, 0, {
                'usr_id': self.pool.get('hr.employee').get_employee(cr, user, user).id,
                'state': self.get_state(next_state)[1]
            })]})

        for attachment in vals.get('attachment_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'kpi.kpi'

        period_id = vals.get('period_id') or record.period_id.id
        employee_id = vals.get('employee_id') or record.employee_id.id
        employee_data = employee_pool.browse(cr, user, employee_id)

        if record.employee_id.name != employee_data.name or record.job_id != employee_data.job_id or record.parent_id != employee_data.parent_id:
            vals['employee_id'] = employee_data.id
            vals['job_id'] = employee_data.job_id.id
            vals['parent_id'] = employee_data.parent_id.id

        return super(Kpi, self).write(cr, user, ids, vals, context)

    def copy(self, cr, uid, id, default=None, context=None):
        default['history_ids'] = None
        default['period_id'] = None
        default['fact_days'] = None

        return super(Kpi, self).copy(cr, uid, id, default, context),

    def unlink(self, cr, uid, ids, context=None):
        expert_pool = self.pool.get('kpi.expert.assesment')
        mbo_pool = self.pool.get('kpi.mbo')
        sla_pool = self.pool.get('kpi.sla')

        for kpi_id in ids:
            expert_ids = expert_pool.search(cr, 1, [('kpi_id', '=', kpi_id)])
            expert_pool.unlink(cr, 1, expert_ids)

            mbo_ids = mbo_pool.search(cr, 1, [('kpi_id', '=', kpi_id)])
            mbo_pool.unlink(cr, 1, mbo_ids)

            sla_ids = sla_pool.search(cr, 1, [('kpi_id', '=', kpi_id)])
            sla_pool.unlink(cr, 1, sla_ids)

        return super(Kpi, self).unlink(cr, uid, ids, context)

    def action_saved(self, cr, uid, ids, context=None):
        """
            При переводе на этап Сохранен для отчетности ->
                Происходит запись в базу income.report
                При этом осуществляются все необходимые расчеты (см. ТЗ)
            При повторном переходе на этап Сохранен для отчетности
                произойдет не создание объекта а запись в него
                (проверка осуществляется по kpi_id)
        """
        report_pool = self.pool.get('income.report')
        data = self.browse(cr, uid, ids[0])

        values = {
            'kpi_id': ids[0],
            'period_id': data.period_id.name,
            'grade': data.grade or '0',
            'employee_id': data.employee_id.name or 'None',
            'job_id': data.job_id.name or 'None',
            'sv': data.sv.replace('-', '/') or '60/40',
            'total_pay': data.total_pay or 0.0,
            'formal_cash': data.formal_cash or 0.0,
            'formal_tax': data.formal_tax or 0.0,
            'days_worked': data.days or 0,
            'retention': data.retention or 0.0,
            'advance': data.advance or 0.0,
            'award': data.award or 0.0,
        }
        report_id = report_pool.search(cr, uid, [('kpi_id', '=', ids[0])])
        if report_id:
            report_pool.write(cr, uid, report_id, values, context)
        else:
            report_pool.create(cr, uid, values, context)
        print values
        return self.write(cr, uid, ids, {'state': 'saved'}, context)

    def _check_days(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if record.state == 'agreed' and not record.fact_days:
                return False
        return True

    def _check_mbo(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if record.mbo_ids and round(sum(row.weight for row in record.mbo_ids), 2) != float(1.0):
                return False
        return True

    def _check_employment(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if record.state == 'passed' and (record.upsale_employment + record.ink_employment) != 100:
                return False
        return True

    def _check_count_mbo(self, cr, uid, ids, context=None):
        """
            Проверка количества ключевых показателей для одного kpi.
        """
        for record in self.browse(cr, uid, ids):
            if len(record.mbo_ids) > 6:
                return True
        return True

    _constraints = [
        (_check_days,
         'Введите фактическое количество отработанных дней.',
         [u'Фактически отработанные дни']),
        (_check_mbo,
         'Вы не можете выставить суммарный вес ключевых показателей не равным 1.',
         []),
        (_check_employment,
         'Занятость в обеих компаниях, в сумме должна составлять 100%.',
         [u'Занятость в UpSale', u'Занятость в INKSYSTEM']),
        (_check_count_mbo,
         'Количество ключевых показателей не может превышать 6.',
         []),

    ]
Kpi()


class KpiHistory(Model):
    _name = 'kpi.history'
    _description = u'KPI - История переходов'
    _log_create = True
    _order = 'create_date desc'
    _rec_name = 'state'

    _columns = {
        'usr_id': fields.many2one('hr.employee', u'Перевел'),
        'state': fields.char(u'На этап', size=65),
        'create_date': fields.datetime(u'Дата', readonly=True),
        'kpi_id': fields.many2one('kpi.smart', 'Smart', invisible=True),
        'dy_cash': fields.float(''),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: self.pool.get('hr.employee').get_employee(cr, uid, uid).id,
    }
KpiHistory()


class KpiMbo(Model):
    _name = 'kpi.mbo'
    _description = u'KPI - Показатели mbo'
    _order = 'weight DESC'

    def calculate_percent(self, cr, uid, row, context=None):
        """
            Расчет показателя.
                На случай если формулы нет -> проводим стандартный расчет
                    факт*100/план
                Если найдена формула разбиваем её по разделителю ';',
                    и исполняем итерационными, затем что бы использовалось последнее условие
                По просчету округляем до двух знаков
                RETURNS float
        """
        plan = row.plan
        fact = row.fact
        weight = row.weight
        result = 0

        if plan:
            result = fact * 100 / plan

        if row.name.formula and (result or 'plan==0' in row.name.formula or 'fact==0' in row.name.formula):
            formula_table = row.name.formula.split(';')
            for formula in formula_table:
                exec formula

        if not row.name.index_type and result > 100:
            result = 100
        result = round(result, 2) if result else False
        return result

    def _calculate(self, cr, uid, ids, name, arg, context=None):
        """
            Одной формулой считаем Процент выполнения и MBO
            Возвращаем dict {'percentage': [float, 2],
                            'mbo': [float, 2]}
                где ключи названия полей
        """
        res = {}
        data = self.browse(cr, uid, ids, context)
        for row in data:
            percentage = self.calculate_percent(cr, uid, row, context)
            res[row.id] = {
                'percentage': percentage,
                'mbo': round((row.weight * percentage), 2) if percentage else 0,
            }
        return res

    _columns = {
        'kpi_id': fields.many2one('kpi.kpi', u'Связанный KPI', invisible=True),
        'name': fields.many2one(
            'kpi.indicators.reference',
            u'Показатель',
            required=True,
            select="1",
            domain=[('type', '=', 'mbo')]
        ),
        'units': fields.related(
            'name',
            'units',
            type="char",
            string=u"Единицы измерения",
            readonly=True
        ),
        'weight': fields.float(u'Вес', select="1"),
        'previous_period': fields.float(u'Предыдущий период', readonly=True),
        'plan': fields.float(u'План', select="1"),
        'fact': fields.float(u'Факт', select="1"),
        'percentage': fields.function(
            _calculate,
            method=True,
            string=u"Процент выполнения",
            type="float",
            store=True,
            multi='base'
        ),
        'mbo': fields.function(_calculate, method=True, string=u"MBO", type="float", store=True, multi='base'),
    }

    def _count_mbo(self, cr, uid, ids, context=None):
        """
            Проверка количества ключевых показателей для одного kpi.
        """
        for field in self.browse(cr, uid, ids):
            if self.search(cr, uid, [('kpi_id', '=', field.kpi_id.id)], count=True) > 6:
                return False
        return True

    _constraints = [
        #(_count_mbo,
        # 'Количество ключевых показателей не может превышать 6.',
        # []),
    ]
KpiMbo()


class KpiSla(Model):
    _inherit = 'kpi.mbo'
    _name = 'kpi.sla'

    _columns = {
        'name': fields.many2one(
            'kpi.indicators.reference',
            u'Показатель',
            required=True,
            select="1",
            domain=[('type', '=', 'sla')]
        ),
    }
KpiSla()


class KpiSla2(Model):
    _inherit = 'kpi.mbo'
    _name = 'kpi.sla2'

    def calculate_percent(self, cr, uid, row, context=None):
        """
            Расчет показателя.
                На случай если формулы нет -> проводим стандартный расчет
                    факт*100/план
                Если найдена формула разбиваем её по разделителю ';',
                    и исполняем итерационными, затем что бы использовалось последнее условие
                По просчету округляем до двух знаков
                RETURNS float
        """
        plan = row.plan
        fact = row.fact
        weight = row.weight
        result = 0

        if plan:
            result = fact * 100 / plan

        if row.name.formula and (result or 'plan==0' in row.name.formula or 'fact==0' in row.name.formula):
            formula_table = row.name.formula.split(';')
            for formula in formula_table:
                exec formula

        if not row.name.index_type and result > 100:
            result = 100
        result = round(result, 2) if result else False
        return result

    def _calculate(self, cr, uid, ids, name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids, context)
        for row in data:
            percentage = self.calculate_percent(cr, uid, row, context)
            res[row.id] = round((row.weight * percentage), 2) if percentage else 0
        return res

    _columns = {
        'site': fields.char('Сайт', size=200),
        'name': fields.many2one(
            'kpi.indicators.reference',
            u'Показатель',
            required=True,
            select="1",
            domain=[('type', '=', 'sla-2')]
        ),
        'mbo': fields.function(_calculate, method=True, string=u"MBO", type="float", store=True, group_operator="avg"),
    }

    _defaults = {
        'weight': 1
    }
KpiSla2()


class KpiSaleSla(Model):
    _inherit = 'kpi.mbo'
    _name = 'kpi.sla.sale'

    _columns = {
        'name': fields.many2one(
            'kpi.indicators.reference',
            u'Показатель',
            required=True,
            select="1",
            domain=[('type', '=', 'sale')]
        ),
    }

    def set_mbo(self, cr, user, ids):
        mbo_pool = self.pool.get('kpi.mbo')
        for record in self.read(cr, user, ids, ['kpi_id']):
            if record['kpi_id']:
                sale_ids = self.pool.get('kpi.sla.sale').search(cr, user, [('kpi_id', '=', record['kpi_id'][0])])
                mbo = sum(x['mbo'] for x in self.read(cr, user, sale_ids, ['mbo']))
                mbo_ids = mbo_pool.search(cr, user, [('kpi_id', '=', record['kpi_id'][0]), ('name', '=', 285)])
                if mbo_ids:
                    mbo_pool.write(cr, user, mbo_ids, {'fact': mbo})

    def write(self, cr, user, ids, vals, context=None):
        flag = super(KpiSaleSla, self).write(cr, user, ids, vals, context)
        self.set_mbo(cr, user, ids)
        return flag

    def create(self, cr, user, vals, context=None):
        item_id = super(KpiSaleSla, self).create(cr, user, vals, context)
        self.write(cr, user, [item_id], {})
        return item_id
KpiSaleSla()


class KpiExpertAssessments(Model):
    """
        Объект Экспертных оценок.
        Связи из других модулей:
            one2many - KPI
        Создаёт экспертные оценки и отправляет их пользователю.
    """
    _name = "kpi.expert.assesment"
    _description = u'KPI - Экспертная оценка'
    _order = 'period_id desc'

    def _get_comment(self, cr, user, ids, name, arg, context=None):
        result = {}

        for record in self.browse(cr, user, ids, context):
            comment = ''
            if name == "client_comments":
                if record.client_note1:
                    comment += "%s. " % record.client_note1
                if record.client_note2:
                    comment += "%s. " % record.client_note2
                if record.client_note3:
                    comment += "%s." % record.client_note3

            if name == "standards_comments":
                if record.standards_note1:
                    comment += "%s. " % record.standards_note1
                if record.standards_note2:
                    comment += "%s. " % record.standards_note2
                if record.standards_note3:
                    comment += "%s." % record.standards_note3

            if name == "quality_comments":
                if record.quality_note1:
                    comment += "%s. " % record.quality_note1
                if record.quality_note2:
                    comment += "%s. " % record.quality_note2
                if record.quality_note3:
                    comment += "%s." % record.quality_note3

            result[record.id] = comment
        return result

    def _calculate_mean(self, cr, uid, ids, name, arg, context=None):
        """
            Расчет средней оценки.
            Если показатели не самоотвод:
                Суммируем и делим на их количество.
                Округляем до двух знаков после запятой.
        """
        result = {}

        def compute_value(*args):
            if u'самоотвод' in args:
                return False
            else:
                return round(numpy.mean([map(float, args)]), 2)

        data = self.browse(cr, uid, ids, context)
        for row in data:
            result[row.id] = compute_value(row.client, row.standards, row.quality)
        return result

    def default_expert(self, cr, uid, context=None):
        """
            При создании из меню:
                Устанавливает стандартным экспертом, сотрудника
                к которому привязан пользователь
            RETURN id объекта hr.employee
        """
        expert_id = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        if expert_id:
            return expert_id[0]
        else:
            return False

    def calculate_average_exp(self, cr, uid, kpi_id, context=None):
        """
            Метод для расчета средней оценки по всем оценка одного KPI.
            @data - browse_record(kpi.kpi, [id])
            Записывает расчитанные значения в соотв показатель mbo.
            !! Необходимо для того, что бы изменения расчитывались при каждом
                действии с любой оценкой KPI
        """
        kpi_pool = self.pool.get('kpi.kpi')
        ids = self.search(cr, 1, [('kpi_id', '=', kpi_id), ('state', '=', 'work')])
        result = 0.0
        if ids:
            result = round(numpy.mean([r['mean'] for r in self.read(cr, 1, ids, ['mean'])]), 2) or 0.0

        mbo_ids = self.pool.get('kpi.mbo').search(cr, 1, [('name', '=', 5), ('kpi_id', '=', kpi_id)])
        if mbo_ids:
            self.pool.get('kpi.mbo').write(cr, 1, mbo_ids, {'fact': result})
            total_mbo = kpi_pool._calculate_total_mbo(cr, 1, [kpi_id], 'total_mbo', [], context)[kpi_id]
            kpi_pool.write(cr, 1, [kpi_id], {'total_mbo': total_mbo})
        return True

    def action_draft(self, cr, uid, ids, context=None):
        """
            При переводе в draft оценка не отображается.
            Соотв. необходимо пересчитать.
        """
        self.write(cr, uid, ids, {'state': 'draft'}, context)
        data = self.read(cr, uid, ids[0], ['kpi_id'])
        self.calculate_average_exp(cr, uid, data['kpi_id'][0], context)
        return True

    def action_work(self, cr, uid, ids, context=None):
        """
            При отправке оценок:
            Происходит проверка наличия kpi.
            В случае наличия происходит расчет и запись общей оценки.
        """
        for record in self.read(cr, uid, ids, ['kpi_id']):
            self.write(cr, uid, ids, {'state': 'work', 'kpi_id': record['kpi_id'][0]}, context)
            self.calculate_average_exp(cr, uid, record['kpi_id'][0], context)
        return True

    _columns = {
        'kpi_id': fields.many2one('kpi.kpi', u'Связанный KPI', invisible=True),
        'expert_id': fields.many2one('hr.employee', u'Эксперт', readonly=True, select="1"),
        'employee_id': fields.many2one(
            'hr.employee',
            u'Сотрудник',
            required=True,
            select="1",
            states={'work': [('readonly', True)]}),
        'period_id': fields.many2one('kpi.period', u'Период', states={'work': [('readonly', True)]}),
        'client': fields.selection(
            [
                ('-2', '-2'),
                ('-1', '-1'),
                ('0', '0'),
                ('1', '+1'),
                ('2', '+2'),
                ('самоотвод', u'самоотвод')
            ], u'Клиентоориентированность, оценка', states={'work': [('readonly', True)]}),
        'client_note1': fields.text(u'Примечание 1', states={'work': [('readonly', True)]}),
        'client_note2': fields.text(u'Примечание 2', states={'work': [('readonly', True)]}),
        'client_note3': fields.text(u'Примечание 3', states={'work': [('readonly', True)]}),
        'standards': fields.selection(
            [
                ('-2', '-2'),
                ('-1', '-1'),
                ('0', '0'),
                ('1', '+1'),
                ('2', '+2'),
                ('самоотвод', u'самоотвод')
            ], u'Соблюдение стандартов, оценка', states={'work': [('readonly', True)]}),
        'standards_note1': fields.text(u'Примечание 1', states={'work': [('readonly', True)]}),
        'standards_note2': fields.text(u'Примечание 2', states={'work': [('readonly', True)]}),
        'standards_note3': fields.text(u'Примечание 3', states={'work': [('readonly', True)]}),
        'quality': fields.selection(
            [
                ('-2', '-2'),
                ('-1', '-1'),
                ('0', '0'),
                ('1', '+1'),
                ('2', '+2'),
                ('самоотвод', u'самоотвод')
            ], u'Качество работы, оценка', states={'work': [('readonly', True)]}),
        'quality_note1': fields.text(u'Примечание 1', states={'work': [('readonly', True)]}),
        'quality_note2': fields.text(u'Примечание 2', states={'work': [('readonly', True)]}),
        'quality_note3': fields.text(u'Примечание 3', states={'work': [('readonly', True)]}),
        'mean': fields.function(
            _calculate_mean,
            method=True,
            string=u"Среднее значение",
            type="float",
            store=True
        ),
        'state': fields.selection([('draft', u'Черновик'), ('work', u'Отправлена')], u'Состояние', readonly=True),

        'client_comments': fields.function(
            _get_comment,
            method=True,
            string=u"Клиентоориентированность, комментарии",
            type="text"
        ),
        'quality_comments': fields.function(
            _get_comment,
            method=True,
            string=u"Качество работы, комментарии",
            type="text"
        ),
        'standards_comments': fields.function(
            _get_comment,
            method=True,
            string=u"Соблюдение стандартов, комментарии",
            type="text"
        ),
    }

    _defaults = {
        'state': 'draft',
        'expert_id': lambda self, cr, uid, context: self.default_expert(cr, uid, context),
    }

    def _check_samootvod(self, cr, uid, ids, context=None):
        """
            Проверка самоотвода.
            Если по одному показателю стоит самоотвод,
            ему должны быть равны все 3 показателя.
        """

        def count(checklist):
            count_int = 0
            result = True
            for item in checklist:
                if u'самоотвод' == item:
                    result = False
                    count_int += 1
            if count_int == 3:
                result = True
            return result

        data = self.browse(cr, uid, ids)[0]
        return count((data.client, data.standards, data.quality))

    def _check_expert(self, cr, uid, ids, context=None):
        """
            Проверка наличия в списке экспертов.
            Если владелец оценки есть у сотрудника в экспертах
            Вернет True
        """
        data = self.read(cr, uid, ids[0], ['employee_id', 'period_id', 'state', 'expert_id'])
        if data['state'] == 'work':
            employee = data['employee_id'][0]
            period = data['period_id'][0]
            kpi_pool = self.pool.get('kpi.kpi')
            kpi_id = kpi_pool.search(cr, 1, [('period_id', '=', period), ('employee_id', '=', employee)])

            if not kpi_id:
                return False
            kpi_data = kpi_pool.read(cr, 1, kpi_id[0], ['experts_ids'])

            if data['expert_id'][0] not in kpi_data['experts_ids']:
                return False
        return True

    def _check_comments(self, cr, uid, ids, context=None):
        """
            Проверка комментариев.
            Если оценка не 0 и не самоотвод:
                Должны быть заполнены 3 комментария каждого типа
        """
        data = self.read(cr, uid, ids[0], ['client_note1', 'client_note2', 'client_note3',
                                           'standards_note1', 'standards_note2', 'standards_note3',
                                           'quality_note1', 'quality_note2', 'quality_note3',
                                           'client', 'standards', 'quality', 'state'])
        options = (data['quality'], data['client'], data['standards'])
        notes = ((data['quality_note1'], data['quality_note2'], data['quality_note3']),
                 ((data['client_note1'], data['client_note2'], data['client_note3'])),
                 ((data['standards_note1'], data['standards_note2'], data['standards_note3'])))
        for option, note in zip(options, notes):
            if option in ('-2', '-1', '1', '2') and False in note:
                return False
        return True

    def _check_unique_per_month(self, cr, uid, ids, context=None):
        """
            Проверка уникальности.
            На конкретный период конкретному сотруднику один и тот же эксперт
            задания установить не может.
        """
        for record in self.browse(cr, uid, ids, context):
            if self.search(cr, uid,
                           [('period_id', '=', record.period_id.id), ('employee_id', '=', record.employee_id.id),
                            ('expert_id', '=', record.expert_id.id), ('id', '!=', record.id)]):
                return False
        return True

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        period_pool = self.pool.get('kpi.period')
        period = [item for item in args if item[0] == 'period_id']

        if period:
            if isinstance(period[0][2], (tuple, list)):
                period_id = period[0][2][0]
            else:
                period_id = period[0][2]
            period_name = period_pool.browse(cr, user, period_id)

            domain = [('name', '=', period_name.name)]

            need_period_ids = period_pool.search(cr, user, domain)
            if need_period_ids:
                args.remove(period[0])
                args.append(('period_id', 'in', need_period_ids))
        return super(KpiExpertAssessments, self).search(cr, user, args, offset, limit, order, context, count)

    def create(self, cr, user, vals, context=None):
        v = vals
        return super(KpiExpertAssessments, self).create(cr, user, vals, context)

    _constraints = [
        (_check_comments,
         'В случае, если вы поставили оценку отличную от 0 - заполните 3 комментария.',
         [u'Комментарии']),
        (_check_samootvod,
         'В случае выбора варианта самоотвод в значениях показателя, ему должны быть равны все.',
         [u'Клиентоориентированность', u'Соблюдение стандартов', u'Качество работы']),
        (_check_expert,
         'Вы не являетесь экспертом у этого сотрудника, либо он не создал KPI',
         []),
        (_check_unique_per_month,
         'Вы не можете выставить более одной экспертной оценки в месяц, конкретному сотруднику.',
         []),
    ]
KpiExpertAssessments()