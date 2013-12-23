# coding=utf-8
import datetime
import pytz
from openerp.osv import fields, osv
from openerp.osv.orm import Model, AbstractModel
from notify import notify


STATES = (
    ('coordination', 'Согласование заявки на запуск'),
    ('filling_TK', 'Заполнение ТЗ'),
    ('revision_TK', 'ТЗ на доработке'),
    ('approval_TK', 'Согласование ТЗ'),

    ('filling_scenario', 'Подготовка сценария'),
    ('revision_scenario', 'Сценарий на доработке'),
    ('approval_scenario', 'Утверждение сценария'),

    ('training_agents', 'Обучение агентов'),
    ('testing_agents', 'Тестирование агентов партнером'),
    ('tech_setup', 'Тех. настройка проекта'),

    ('filling_template', 'Подготовка формы отчета'),
    ('revision_template', 'Форма отчета на доработке'),
    ('approval_template', 'Согласование формы отчета'),

    ('development', 'Реализация проекта'),
    ('pause', 'Приостановление проекта'),
    ('coordination_reporting', 'Согласование отчетности'),
    ('finish', 'Проект завершен'),
)


class ProcessCallIn(Model):
    _name = 'process.call.in'
    _inherit = 'process.call'
    _description = u'Процессы - Call - Исходящая кампания'

    _columns = {
        'state': fields.selection(STATES, 'статус', readonly=True),
        'history_ids': fields.one2many(
            'process.history',
            'process_id',
            'История',
            domain=[('process_model', '=', _name)]),
        'report_ids': fields.one2many(
            'process.reports',
            'process_id',
            'Отчеты',
            domain=[('process_model', '=', _name)]),
        'message_ids': fields.one2many(
            'process.messages',
            'process_id',
            'Переписка по проекту',
            domain=[('process_model', '=', _name)]),

        'employees_for_training_ids': fields.many2many(
            'hr.employee',
            'empl_in_comp_training_rel',
            'in_comp_id',
            'employee_id',
            string='Список сотрудников для обучения',
            select=True),
        'employees_aprov_partner_ids': fields.many2many(
            'hr.employee',
            'empl_in_comp_aprov_rel',
            'in_comp_id',
            'employee_id',
            string='Список утвержденных партнером сотрудников',
            select=True,
            domain="[('id','in',employees_for_training_ids[0][2])]"),

        'sla_ids': fields.one2many(
            'process.sla',
            'process_id',
            'SLA',
            domain=[('process_model', '=', _name)],
            context={'type': 'call', 'process_model': _name}),

        'surcharge_ids': fields.one2many(
            'process.call.surcharge',
            'process_id',
            'Доплаты',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),

        'logic_cols': fields.text('Алгоритм распределения звонков в очереди'),
        'turn_proj': fields.text('Очереди по проекту'),
        'schedule_ids': fields.one2many(
            'process.call.in.schedule',
            'process_id',
            'Расписание',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),
        'scenario_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Дополнения к сценарию',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'scenario_files')]),
        'fact_ids': fields.one2many('report.day.call.in.static', 'process_call_in_id', 'Факты'),
        'queue': fields.integer('Очередь'),
    }

    _defaults = {
        'state': 'coordination',
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        error = []
        line_ids = []

        for record in self.read(cr, uid, ids, []):
            next_state = values.get('state', False)
            state = record['state']

            if values.get('specialist_id'):
                line_ids += self.pool.get('process.launch')._get_pay_ids(cr, uid, [record['launch_id'][0]], '', {})[record['launch_id'][0]]['invoice_pay_ids']

            if next_state and next_state != state:
                if next_state == 'filling_TK':
                    if not values.get('prep_days', False) and not record['prep_days']:
                        error.append('Необходимо ввести количество рабочих дней на подготовку проекта')
                    if not values.get('specialist_id', False) and not record['specialist_id']:
                        error.append('Необходимо выбрать супервайзера проекта')

                if state == 'filling_TK' and next_state == 'approval_TK' and (not values.get('tz_filled_file_id', False) and not record['tz_filled_file_id']):
                    error.append('Необходимо прикрепить заполненное ТЗ')

                if state == 'approval_TK':
                    if next_state == 'revision_TK' and (not values.get('re_tz_commentary', False) and not record['re_tz_commentary']):
                        error.append('Необходимо ввести комментарий по доработке ТЗ')

                if state == 'filling_scenario' and next_state == 'approval_scenario' and (not values.get('prior_scenario_file_id', False) and not record['prior_scenario_file_id']):
                    error.append('Необходимо прикрепить предварительный сценарий')

                if state == 'approval_scenario' and next_state == 'revision_scenario' and (not values.get('scenario_comment', False) and not record['scenario_comment']):
                    error.append('Необходимо ввести комментарий по доработке сценария')

                if state == 'approval_scenario' and next_state == 'training_agents' and (not values.get('employees_for_training_ids', False) and not record['employees_for_training_ids']):
                    error.append('Необходимо добавить сотрудников для обучения')

                if state == 'training_agents' and next_state == 'testing_agents' and (not values.get('employees_for_training_ids', False) and not record['employees_for_training_ids']):
                    error.append('Необходимо добавить список утвержденных партнером сотрудников')

                if state == 'testing_agents' and next_state == 'tech_setup':
                    if not values.get('logic_cols', False) and not record['logic_cols']:
                        error.append('Необходимо ввести алгоритм распределения звонков в очереди')
                    if not values.get('settings_email', False) and not record['settings_email']:
                        error.append('Необходимо ввести настройки электронной почты')
                    if not values.get('inner_phone_ids', False) and not record['inner_phone_ids']:
                        error.append('Необходимо ввести внутренние номера проекта')
                    if not values.get('turn_proj', False) and not record['turn_proj']:
                        error.append('Необходимо ввести очереди по проекту')

                if next_state == 'filling_template' and (not values.get('template_report_id', False) and not record['template_report_id']):
                    error.append('Необходимо добавить файл формы отчета')

                if next_state == 'development':
                    if not values.get('report_ids', False) and not record['report_ids']:
                        error.append('Необходимо добавить отчеты')

                if error:
                    raise osv.except_osv("Входящая кампания", ', '.join(error))

                values.update({
                    'history_ids': [
                        (0, 0, {
                            'state': self.get_state(STATES, next_state)[1],
                            'process_model': self._name
                        })
                    ]})
        flag = super(ProcessCallIn, self).write(cr, uid, ids, values, context)
        if flag and line_ids and values.get('specialist_id'):
            self.pool.get('account.invoice.pay.line').write(cr, uid, line_ids, {'specialist_id': values['specialist_id']})
        return flag
ProcessCallIn()


class ProcessCallInSchedule(Model):
    _name = 'process.call.in.schedule'
    _inherit = 'process.base.staff'

    _columns = {
        'name': fields.char('Дни недели', size=250),
        'comment': fields.char('Время работы', size=250),
    }
ProcessCallInSchedule()