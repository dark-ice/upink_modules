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

    ('filling_db', 'Подготовка контактной базы'),
    ('revision_db', 'Контактная база на доработке'),
    ('approval_db', 'Согласование контактной базы'),

    ('filling_template', 'Подготовка формы отчета'),
    ('revision_template', 'Форма отчета на доработке'),
    ('approval_template', 'Согласование формы отчета'),


    ('training_agents', 'Обучение агентов'),
    ('testing_agents', 'Тестирование агентов партнером'),

    ('tech_setup', 'Тех. настройка проекта'),
    ('development', 'Реализация проекта'),
    ('pause', 'Приостановление проекта'),
    ('coordination_reporting', 'Согласование отчетности'),
    ('billing_surcharge', 'Выставление счета на доплату'),
    ('finish', 'Проект завершен'),
)


class ProcessCallOut(Model):
    _name = 'process.call.out'
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
        'tz_filled_file_id': fields.many2one('ir.attachment', 'Заполненное ТЗ'),
        're_tz_commentary': fields.text('Комментарии по доработке'),

        'db_type': fields.selection(
            [
                ('partner', 'партнер'),
                ('upsale', 'Upsale')
            ], 'Тип базы данных'),

        'db_file_id': fields.many2one(
            'ir.attachment',
            'База данных по проекту',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'db')]),

        'contact_num': fields.integer('Количество контактов'),

        'employees_for_training_ids': fields.many2many(
            'hr.employee',
            'empl_out_comp_training_rel',
            'out_comp_id',
            'employee_id',
            string='Список сотрудников для обучения',
            select=True),
        'employees_aprov_partner_ids': fields.many2many(
            'hr.employee',
            'empl_out_comp_aprov_rel',
            'out_comp_id',
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

        'materials_id': fields.many2one(
            'ir.attachment',
            'Материалы для рассылки',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'materials')]),
        'account_ids': fields.one2many(
            'account.invoice',
            'partner_id',
            'Счета на доплату',
            domain=[('type', '=', 'out_invoice')],
        )
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
                    if not values.get('report_type', False) and not record['report_type']:
                        error.append('Необходимо выбрать тип отчетности')
                    if not values.get('prep_days', False) and not record['prep_days']:
                        error.append('Необходимо ввести количество рабочих дней на подготовку проекта')
                    if not values.get('specialist_id', False) and not record['specialist_id']:
                        error.append('Необходимо выбрать супервайзера проекта')

                if next_state == 'approval_TK':
                    if not values.get('tz_filled_file_id', False) and not record['tz_filled_file_id']:
                        error.append('Необходимо добавить заполненное ТЗ')
                    if not values.get('db_type', False) and not record['db_type']:
                        error.append('Необходимо выбрать тип базы данных')
                    if not values.get('db_file_id', False) and not record['db_file_id']:
                        error.append('Необходимо добавить базу данных по проекту')
                    if not values.get('contact_num', False) and not record['contact_num']:
                        error.append('Необходимо ввести количество контактов')

                if next_state == 'revision_TK' and (not values.get('re_tz_commentary', False) and not record['re_tz_commentary']):
                    error.append('Необходимо ввести комментарий по доработке ТЗ')

                if state == 'filling_scenario' and next_state == 'approval_scenario' and (not values.get('prior_scenario_file_id', False) and not record['prior_scenario_file_id']):
                    error.append('Необходимо прикрепить предварительный сценарий')

                if state == 'approval_scenario' and next_state == 'revision_scenario' and (not values.get('scenario_comment', False) and not record['scenario_comment']):
                    error.append('Необходимо ввести комментарий по доработке сценария')

                if next_state == 'filling_template' and (not values.get('template_report_id', False) and not record['template_report_id']):
                    error.append('Необходимо добавить файл формы отчета')

                if next_state == 'training_agents' and (not values.get('employees_for_training_ids', False) and not record['employees_for_training_ids']):
                    error.append('Необходимо добавить сотрудников для обучения')

                if state == 'training_agents' and next_state == 'testing_agents' and (not values.get('employees_for_training_ids', False) and not record['employees_for_training_ids']):
                    error.append('Необходимо добавить список утвержденных партнером сотрудников')

                if next_state == 'tech_setup':
                    if not values.get('settings_email', False) and not record['settings_email']:
                        error.append('Необходимо ввести настройки электронной почты')
                    if not values.get('inner_phone_ids', False) and not record['inner_phone_ids']:
                        error.append('Необходимо ввести внутренние номера проекта')
                    if not values.get('aoh', False) and not record['aoh']:
                        error.append('Необходимо ввести АОН')

                if next_state == 'development':
                    if not values.get('report_ids', False) and not record['report_ids']:
                        error.append('Необходимо добавить отчеты')

                if next_state == 'billing_surcharge' and (not values.get('surcharge_ids', False) and not record['surcharge_ids']):
                    error.append('Необходимо ввести доплаты')

                if error:
                    raise osv.except_osv("Исходящая кампания", ', '.join(error))

                values.update({
                    'history_ids': [
                        (0, 0, {
                            'state': self.get_state(STATES, next_state)[1],
                            'process_model': self._name
                        })
                    ]})
        flag = super(ProcessCallOut, self).write(cr, uid, ids, values, context)
        if flag and line_ids and values.get('specialist_id'):
            self.pool.get('account.invoice.pay.line').write(cr, uid, line_ids, {'specialist_id': values['specialist_id']})
        return flag
ProcessCallOut()