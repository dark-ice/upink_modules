# coding=utf-8
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify


STATES = (
    ('coordination', 'Согласование заявки на запуск'),
    ('drafting', 'Подготовка запуска кампании'),
    ('revision', 'Доработка кампании'),
    ('approval', 'Утверждение кампании'),
    ('implementation', 'Реализация кампании'),
    ('finish', 'Кампания остановлена'),
)


class ProcessPPC(Model):
    _name = 'process.ppc'
    _inherit = 'process.base'
    _description = u'Процессы - PPC'
    _rec_name = 'launch_id'
    _order = 'create_date desc'

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

            #  Координатор
            if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', '=', 108)]):
                access += 'k'

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
            'Аккаунт менеджер',
            select=True,
            domain="[('groups_id','in',[107])]",
        ),  # Специалист направления PPC

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
            context={'type': 'ppc', 'process_model': _name}),

        'access_ids': fields.one2many(
            'process.ppc.access',
            'process_id',
            'Доступы',
            readonly=True,
            states={
                'drafting': [('readonly', False), ('required', True)],
                'revision': [('readonly', False)],
            }),
        'additional_data_company': fields.text(
            'Дополнительные данные по кампании'
        ),
        'reason_stop_company': fields.text(
            'Причина остановки кампании',
            readonly=True,
            states={
                'implementation': [('readonly', False), ('required', True)]
            }
        ),

        'comment': fields.text(
            'Комментарий по доработке',
            readonly=True,
            states={
                'approval': [('readonly', False)]
            }
        ),

        'deadline': fields.datetime(
            'Дедлайн на следующее состояние',
            readonly=True),

        'advertising_id': fields.many2one(
            'process.ppc.advertising',
            'Рекламная система',
            select=True,
            readonly=True,
            states={
                'coordination': [('readonly', False)],
                'drafting': [('readonly', False), ('required', True)]
            }),

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
        'check_k': fields.function(
            _check_access,
            method=True,
            string='Проверка на координатор',
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
        for record in self.read(cr, uid, ids, ['state', 'specialist_id', 'comment', 'reason_stop_company', 'advertising_id', 'access_ids', 'launch_id']):
            next_state = values.get('state', False)
            state = record['state']

            if values.get('specialist_id'):
                line_ids += self.pool.get('process.launch')._get_pay_ids(cr, uid, [record['launch_id'][0]], '', {})[record['launch_id'][0]]['invoice_pay_ids']

            if next_state and next_state != state:
                if next_state == 'drafting' and (not values.get('specialist_id', False) and not record['specialist_id']):
                    error += 'Необходимо выбрать специалиста'
                if next_state == 'revision' and (not values.get('comment', False) and not record['comment']):
                    error += 'Необходимо ввести комментарий по доработке'
                if next_state == 'finish' and (not values.get('reason_stop_company', False) and not record['reason_stop_company']):
                    error += 'Необходимо ввести причину остановки работ'
                if next_state == 'approval':
                    if not values.get('advertising_id', False) and not record['advertising_id']:
                        error += 'Необходимо выбрать рекламная система'
                    if not values.get('access_ids', False) and not record['access_ids']:
                        error += 'Необходимо ввести доступы'

                if error:
                    raise osv.except_osv("PPC", error)

                values.update({
                    'history_ids': [
                        (0, 0, {
                            'state': self.get_state(STATES, next_state)[1],
                            'process_model': self._name
                        })
                    ]})
        flag = super(ProcessPPC, self).write(cr, uid, ids, values, context)
        if flag and line_ids and values.get('specialist_id'):
            self.pool.get('account.invoice.pay.line').write(cr, uid, line_ids, {'specialist_id': values['specialist_id']})
        return flag
ProcessPPC()


class ProcessPPCAccess(Model):
    _name = 'process.ppc.access'
    _description = u'Процессы - PPC - Доступы'

    _columns = {
        'advertising_id': fields.many2one('process.ppc.advertising', 'Рекламная система'),
        'login': fields.char('Логин', size=250),
        'password': fields.char('Пароль', size=64),
        'process_id': fields.many2one('process.ppc', 'PPC', invisible=True),
    }
ProcessPPCAccess()


class ProcessPPCAdvertising(Model):
    _name = "process.ppc.advertising"
    _description = u"PPC рекламная система - справочник"
    _columns = {
        'name': fields.char('Название', size=165, required=True),
    }
ProcessPPCAdvertising()
