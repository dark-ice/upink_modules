# coding=utf-8
import datetime
import pytz
from openerp.osv import fields, osv
from openerp.osv.orm import Model, AbstractModel
from notify import notify


def get_count_day(first_day_index, count_work_days):
    """
    Количество календарных дней начиная с дня недели(first_day) и имея work_days рабочих дней
    @first_day - int(0-6)
    @work_days - int

    @return int
    """
    count_work_days = abs(count_work_days)
    if first_day_index < 0:
        first_day_index = 0
    if first_day_index > 6:
        first_day_index = 6
    full_week_count = count_work_days / 5 + 1
    if count_work_days + first_day_index > 5 and full_week_count == 1:
        full_week_count = 2
    full_days_count = 7 * full_week_count - 1
    weekends_count = 2 * (full_week_count - 1)
    if first_day_index > 4:
        weekends_count -= 7 - first_day_index
    last_day_index = full_days_count - first_day_index - count_work_days - weekends_count
    return full_days_count - last_day_index - first_day_index


class ProcessCall(AbstractModel):
    _name = 'process.call'
    _inherit = 'process.base'
    _description = u'Процессы - Call'
    _rec_name = 'launch_id'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['responsible_id'], context):
            access = str()

            #  Менеджер
            if data.get('responsible_id') and data['responsible_id'][0] == uid:
                access += 'a'

            #  Супервайзер и руководитель Call
            if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', [81, 93])]):
                access += 'm'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[data['id']] = val
        return res

    def _deadline_start(self, cr, uid, ids, field_name, arg, context):
        result = {}
        for obj in self.read(cr, uid, ids, ['pay_date', 'prep_days'], context=context):
            start_date = datetime.datetime.now(pytz.utc).date()
            if obj['pay_date']:
                start_date = datetime.datetime.strptime(obj['pay_date'], "%Y-%m-%d").replace(tzinfo=pytz.utc).date()
            if obj['prep_days']:
                result[obj['id']] = start_date + datetime.timedelta(days=get_count_day(start_date.weekday(), obj['prep_days']))
        return result

    def _get_pay_date(self, cr, uid, ids, field_name, arg, context):
        res = {}
        line_pool = self.pool.get('account.invoice.pay.line')
        for record in self.read(cr, uid, ids, ['service_id', 'account_id', 'account_date']):
            pay_date = None
            if record['account_id']:
                pay_line_ids = line_pool.search(
                    cr,
                    uid,
                    [
                        ('invoice_id', '=', record['account_id'][0]),
                        ('service_id', '=', record['service_id'][0])
                    ],
                    order='pay_date')
                for line in line_pool.read(cr, uid, pay_line_ids, ['pay_date']):
                    pay_date = line['pay_date']
                    break
                else:
                    pay_date = record['account_date']
            res[record['id']] = pay_date
        return res

    _columns = {
        'specialist_id': fields.many2one(
            'res.users',
            'Супервайзер проекта',
            select=True,
            domain="[('groups_id','in',[103])]",
            readonly=True,
            states={
                'coordination': [('readonly', False)]
            }
        ),  # Специалист направления Call


        #'state': fields.selection(STATES, 'статус', readonly=True),


        'prep_days': fields.integer('Количество рабочих дней на подготовку проекта'),
        'pay_date': fields.function(
            _get_pay_date,
            type='date',
            method=True,
            store=True,
            string='Дата оплат'
        ),
        'start_line': fields.function(
            _deadline_start,
            type='date',
            method=True,
            store=True,
            string='Дедлайн по запуску проекта',
            select=True),

        'file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'ТЗ',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'files')]),

        'report_type': fields.selection(
            (
                ('daily', 'ежедневная'),
                ('weekly', 'еженедельная'),
                ('monthly', 'ежемесячная'),
                ('result', 'по результатам проекта'),
            ), 'Тип отчетности'
        ),

        #Тех настройка
        'inner_phone_ids': fields.one2many(
            'process.call.inner.phone',
            'process_id',
            'Внутренние номера проекта'
        ),

        # Сценарии
        'prior_scenario_file_id': fields.many2one(
            'ir.attachment',
            'Предварительный сценарий',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'prior_scenario')]),
        'scenario_file_id': fields.many2one(
            'ir.attachment',
            'Сценарий с дополнениями',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'scenario')]),
        'scenario_comment': fields.text('Комментарии по доработке'),

        'aoh': fields.one2many('process.call.aoh', 'process_id', 'АОН'),
        'settings_email': fields.text('Настройки электронной почты'),

        'tz_filled_file_id': fields.many2one('ir.attachment', 'Заполненное ТЗ'),
        're_tz_commentary': fields.text('Комментарии по доработке'),
        'template_report_id': fields.many2one('ir.attachment', 'Форма отчета'),

        'check_a': fields.function(
            _check_access,
            method=True,
            string='Проверка на менеджера',
            type='boolean',
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string='Проверка call',
            type='boolean',
            invisible=True
        ),
    }

    def write(self, cr, uid, ids, values, context=None):
        for key in ['report_ids', 'message_ids', 'file_ids']:
            for item in values.get(key, []):
                if item[0] == 0:
                    item[2]['process_model'] = self._name
        return super(ProcessCall, self).write(cr, uid, ids, values, context)


class ProcessCallReport(Model):
    _name = 'process.call.report'
    _inherit = 'process.base.staff'
    _description = u'Процессы - CALL - Отчеты'

    _columns = {
        'type': fields.selection([
            ('finance', 'Финансовый отчет'),
            ('analitic', 'Аналитический отчет'),
            ('static', 'Статистический отчет'),
            ('total', 'Общий отчет'),
        ], 'Тип отчета'),
        'attachment_id': fields.many2one(
            'ir.attachment',
            'Прикрепленный файл',
            domain=[('res_model', '=', _name)]),
        'date_to': fields.datetime('Дата предоставления отчета'),
    }
ProcessCallReport()


class ProcessCallInnerPhone(Model):
    _name = 'process.call.inner.phone'
    _inherit = 'process.base.staff'
    _description = u'Процессы - CALL - Внутренние номера проекта'

    _columns = {
        'name': fields.char('Номер', size=56, required=True, select=True),
    }
ProcessCallInnerPhone()


class ProcessCallAOH(Model):
    _name = 'process.call.aoh'
    _inherit = 'process.base.staff'
    _description = u'Процессы - CALL - АОН'

    _columns = {
        'name': fields.char('Номер', size=15, required=True),
    }
ProcessCallInnerPhone()


class ProcessCallSurcharge(Model):
    _name = 'process.call.surcharge'
    _inherit = 'process.base.staff'
    _description = u'Процессы - CALL - Доплаты'

    _columns = {
        'name': fields.float('Сумма $'),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'period_name': fields.related(
            'period_id',
            'name',
            type='char',
            size=7,
            store=True
        ),
        'pay_date': fields.date('Желаемая дата оплаты'),
        'get': fields.boolean('Доплата получена')
    }
ProcessCallInnerPhone()