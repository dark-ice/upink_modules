# coding=utf-8
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify


STATES = (
    ('coordination', 'Согласование заявки на запуск'),
    ('creating', 'Создание документации'),
    ('revision', 'Доработка'),
    ('agreement', 'Согласование регламентирующей документации с партнером'),
    ('work', 'Работа по проекту'),
    ('finish', 'Работы закончены'),
)


class ProcessSMM(Model):
    _name = 'process.smm'
    _inherit = 'process.base'
    _description = u'Процессы - SMM'
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
            domain="[('groups_id','in',[80])]",
            readonly=True,
            states={
                'coordination': [('readonly', False), ('required', True)]
            }),  # Специалист направления SMM


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

        'targeted_advertising': fields.related(
            'launch_id',
            'targeted_advertising',
            string='Таргетированная реклама',
            type='boolean',
            readonly=True
        ),
        'lead_management': fields.related(
            'launch_id',
            'lead_management',
            string='Лид менеджмент',
            type='boolean',
            readonly=True
        ),
        'hidden_marketing': fields.related(
            'launch_id',
            'hidden_marketing',
            string='Скрытый маркетинг',
            type='boolean',
            readonly=True
        ),
        'reputation_management': fields.related(
            'launch_id',
            'reputation_management',
            string='Продвижение в соц. сетях',
            type='boolean',
            readonly=True
        ),

        'date_partners_from': fields.related(
            'launch_id',
            'date_partners_from',
            string='c',
            type='date',
            readonly=True
        ),
        'date_partners_to': fields.related(
            'launch_id',
            'date_partners_to',
            string='по',
            type='date',
            readonly=True
        ),

        'file_ids': fields.one2many(
            'process.smm.files',
            'process_id',
            'Документация по проекту',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name},
            readonly=True,
            states={
                'creating': [('readonly', False), ('required', True)],
            }),

        'commentary': fields.text(
            'Комментарий по доработке',
            readonly=True,
            states={
                'agreement': [('readonly', False)]
            }
        ),
        'reason_stop_work': fields.text(
            'Причина остановки работ',
            readonly=True,
            states={
                'work': [('readonly', False)]
            }),

        'sla_ids': fields.one2many(
            'process.sla',
            'process_id',
            'SLA',
            domain=[('process_model', '=', _name)],
            context={'type': 'smm', 'process_model': _name}),

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
        'plan_ids': fields.one2many(
            'report.day.smm.static.plan',
            'process_smm_id',
            'Планы'
        ),
        'fact_ids': fields.one2many(
            'report.day.smm.static.fact',
            'process_smm_id',
            'Факты'
        ),
    }

    _defaults = {
        'state': 'coordination',
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        error = []
        for key in ['report_ids', 'message_ids', 'file_ids']:
            for item in values.get(key, []):
                if item[0] == 0:
                    item[2]['process_model'] = self._name

        line_ids = []
        for record in self.read(cr, uid, ids, ['state', 'file_ids', 'commentary', 'reason_stop_work', 'specialist_id', 'sla_ids', 'report_ids', 'launch_id']):
            next_state = values.get('state', False)
            state = record['state']

            if values.get('specialist_id'):
                line_ids += self.pool.get('process.launch')._get_pay_ids(cr, uid, record['launch_id'][0], '', {})[record['launch_id'][0]]['invoice_pay_ids']

            if next_state and next_state != state:
                if next_state == 'creating' and (not values.get('specialist_id', False) and not record['specialist_id']):
                    error.append('Необходимо выбрать специалиста')
                if next_state == 'agreement' and (not values.get('file_ids', False) and not record['file_ids']):
                    error.append('Необходимо добавить документацию по проекту')
                if next_state == 'revision' and (not values.get('commentary', False) and not record['commentary']):
                    error.append('Необходимо ввести комментарий по доработке')
                if next_state == 'finish':
                    if not values.get('reason_stop_work', False) and not record['reason_stop_work']:
                        error.append('Необходимо ввести причину остановки работ')
                    if not values.get('report_ids', False) and not record['report_ids']:
                        error.append('Необходимо заполнить отчеты')
                    if not values.get('sla_ids', False) and not record['sla_ids']:
                        error.append('Необходимо ввести показатели SLA')

                if error:
                    raise osv.except_osv("SMM", ', '.join(error))

                values.update({
                    'history_ids': [
                        (0, 0, {
                            'state': self.get_state(STATES, next_state)[1],
                            'process_model': self._name
                        })
                    ]})
        flag = super(ProcessSMM, self).write(cr, uid, ids, values, context)
        if flag and line_ids and values.get('specialist_id'):
            self.pool.get('account.invoice.pay.line').write(cr, uid, line_ids, {'specialist_id': values['specialist_id']})
        return flag


ProcessSMM()


class ProcessSMMFiles(Model):
    _name = 'process.smm.files'
    _inherit = 'process.base.staff'
    _description = u'Процессы - SMM - Файлы'

    _columns = {
        'attachment_id': fields.many2one(
            'ir.attachment',
            'Прикрепленный файл',
            domain=[('res_model', '=', _name)],
            context={'res_model': _name},),
        'file_type': fields.selection(
            (
                ('strategy', 'Стратегия'),
                ('announcement', 'Объявление'),
                ('selection_site', 'Подбор площадок'),
                ('monitoring', 'Утверждение слов для мониторинга'),
                ('doc', 'Документация'),
            ), 'Тип'
        )
    }
ProcessSMMFiles()