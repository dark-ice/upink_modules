# coding=utf-8
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify


STATES = (
    ('coordination', 'Согласование заявки на запуск'),
    ('drafting', 'Составление стратегии'),
    ('revision', 'Доработка стратегии'),
    ('approval', 'Утверждение стратегии'),
    ('implementation', 'Реализация стратегии'),
    ('analysis', 'Анализ стратегии'),
    ('finish', 'Работы закончены'),
)


class ProcessSeo(Model):
    _name = 'process.seo'
    _inherit = 'process.base'
    _description = u'Процессы - SEO'
    _rec_name = 'launch_id'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['responsible_id', 'specialist_id', 'service_head_id'], context):
            access = str()

            #  Менеджер
            if data.get('responsible_id') and data['responsible_id'][0] == uid:
                access += 'a'

            #  Специалист
            if data.get('specialist_id') and data['specialist_id'][0] == uid:
                access += 's'

            #  Руководитель
            if data.get('service_head_id') and data['service_head_id'][0] == uid:
                access += 'm'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'specialist_id': fields.many2one(
            'res.users',
            'Ответственный',
            select=True,
            domain="[('groups_id','in',[79])]",
            states={
                'coordination': [('required', True)],
            }),  # Специалист направления SEO

        'promotion_word': fields.boolean('Продвижение по словам'),
        'promotion_traffic': fields.boolean('Продвижение по трафику'),
        'seo_audit': fields.boolean('SEO аудит'),
        'seo_optim': fields.boolean('SEO оптимизация'),
        'promotion_other': fields.boolean('Другой вариант'),
        #
        'strategy_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Стратегия',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'strategy')],
            context={'res_model': _name, 'tmp_res_model': 'strategy'}
        ),
        'reason_stop_work': fields.text(
            'Причина остановки работ',
            readonly=True,
            states={
                'analysis': [('readonly', False)]
            }
        ),
        'comment': fields.text(
            'Комментарий по доработке',
            readonly=True,
            states={
                'approval': [('readonly', False)]
            }
        ),
        'state': fields.selection(STATES, 'статус', readonly=True),

        'history_ids': fields.one2many(
            'process.history',
            'process_id',
            'История',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'report_ids': fields.one2many(
            'process.reports',
            'process_id',
            'Отчеты',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'message_ids': fields.one2many(
            'process.messages',
            'process_id',
            'Переписка по проекту',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'sla_ids': fields.one2many(
            'process.sla',
            'process_id',
            'SLA',
            domain=[('process_model', '=', _name)],
            context={'type': 'seo', 'process_model': _name}),
        'costs_ids': fields.one2many(
            'process.costs',
            'process_id',
            'Затраты на партнера',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),

        'task_ids': fields.one2many('process.seo.tasks', 'process_id', 'Задачи в рамках проекта'),

        'check_a': fields.function(
            _check_access,
            method=True,
            string='Проверка на автора',
            type='boolean',
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string='Проверка на руководителя',
            type='boolean',
            invisible=True
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на специалиста',
            type='boolean',
            invisible=True
        ),
    }

    _defaults = {
        'state': 'coordination',
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        error = ''

        for key in ['report_ids', 'message_ids']:
            for item in values.get(key, []):
                if item[0] == 0:
                    item[2]['process_model'] = self._name
        line_ids = []

        for record in self.read(cr, uid, ids, ['state', 'comment', 'reason_stop_work', 'specialist_id', 'strategy_ids', 'report_ids', 'launch_id']):
            next_state = values.get('state', False)
            state = record['state']

            if values.get('specialist_id'):
                line_ids += self.pool.get('process.launch')._get_pay_ids(cr, uid, [record['launch_id'][0]], '', {})[record['launch_id'][0]]['invoice_pay_ids']

            if next_state and next_state != state:
                if next_state == 'drafting' and (not values.get('specialist_id', False) and not record['specialist_id']):
                    error += 'Необходимо выбрать специалиста'
                if next_state == 'revision' and (not values.get('comment', False) and not record['comment']):
                    error += 'Необходимо ввести комментарий по доработке'
                if next_state == 'approval' and (not values.get('strategy_ids', False) and not record['strategy_ids']):
                    error += 'Необходимо добавить стратегию'
                if next_state == 'implementation' and (not values.get('report_ids', False) and not record['report_ids']):
                    error += 'Необходимо заполнить отчеты'
                if next_state == 'finish' and (not values.get('reason_stop_work', False) and not record['reason_stop_work']):
                    error += 'Необходимо ввести причину остановки работ'

                if error:
                    raise osv.except_osv("SEO", error)

                values.update({
                    'history_ids': [
                        (0, 0, {
                            'state': self.get_state(STATES, next_state)[1],
                            'process_model': self._name
                        })
                    ]})

        flag = super(ProcessSeo, self).write(cr, uid, ids, values, context)
        if flag and line_ids and values.get('specialist_id'):
            self.pool.get('account.invoice.pay.line').write(cr, uid, line_ids, {'specialist_id': values['specialist_id']})
        return flag

    def update(self, cr, uid, ids, context=None):
        return self.pool.get('report.day.seo.statistic').update_positions(cr, ids)
ProcessSeo()


class ProcessSeoTasks(Model):
    _name = "process.seo.tasks"
    _description = u'Процессы - SEO - Задачи в рамках проекта'

    _columns = {
        'name': fields.char('Задача', size=256),
        'create_uid': fields.many2one('res.users', 'Автор записи', readonly=True),
        'date_complete': fields.datetime('Дата выполнения'),
        'process_id': fields.many2one('process.seo', 'SEO', invisible=True),
    }
ProcessSeoTasks()


class ProcessSeoPlan(Model):
    _name = 'process.seo.plan'
    _description = u'Процессы - SEO - Планы ТОП 10'
    _order = 'period_name desc'

    _columns = {
        'name': fields.integer('План'),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')], required=True),
        'period_name': fields.related(
            'period_id',
            'name',
            type='char',
            size=7,
            store=True
        ),
        'seo_id': fields.many2one('process.seo', 'SEO'),
    }
ProcessSeoPlan()
