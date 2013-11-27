# coding=utf-8
import datetime
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify


STATES = (
    ('storage', 'Склад'),
    ('reserve', 'Резерв'),
    ('issued', 'Выдана'),
    ('repair', 'Ремонт'),
    ('on_cancellation', 'На списание'),
    ('cancellation', 'Списана'),
)
TYPE_TECHNIQUE = (
    ('pc', 'ПК'),
    ('notebook', 'Ноутбук'),
    ('monitor', 'Монитор'),
    ('headset', 'Гарнитура'),
    ('mobile', 'Мобильный телефон'),
    ('keyboard', 'Клавиатура'),
    ('mouse', 'Мышь'),
    ('storage', 'Носитель памяти'),
    ('server', 'Сервер'),
    ('commutator', 'Коммутатор'),
    ('switch', 'Свитч'),
    ('network', 'Сетевое оборудование'),
    ('printer', 'Принтер'),
)


class HrTechnique(Model):
    _name = 'hr.technique'
    _description = u'Учет техники'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['cancellation_employee_send_ids'], context):
            access = str()
            val = False
            letter = name[6]

            user_ids = [
                u['user_id'][0]
                for u in self.pool.get('hr.employee').read(cr, 1, data['cancellation_employee_send_ids'], ['user_id'])
                if u['user_id']
            ]
            if uid in user_ids:
                access += 'r'

            if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', [195, 196])]):
                access += 's'

            if letter in access or uid == 1:
                val = True

            res[data['id']] = val
        return res

    def _get_rate(self, cr, uid, ids, name, arg, context=None):
        res = {}
        currency_rate_pool = self.pool.get('res.currency.rate')
        currency_pool = self.pool.get('res.currency')
        for record in self.read(cr, uid, ids, ['date_of_purchase', 'currency_id', 'cash']):
            currency_date_ids = currency_rate_pool.search(
                cr,
                uid,
                [('name', '=', record['date_of_purchase']), ('currency_id', '=', record['currency_id'][0])]
            )
            if currency_date_ids:
                currency = currency_rate_pool.read(cr, uid, currency_date_ids[0], ['rate'])
            else:
                currency = currency_pool.read(cr, uid, record['currency_id'][0], ['rate'])

            res[record['id']] = {
                'rate': currency['rate'],
                'cash_ye': record['cash'] / currency['rate']
            }
        return res

    _columns = {
        'name': fields.char(
            'Название',
            size=256,
            required=True,
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }
        ),
        'state': fields.selection(STATES, 'Статус'),
        'type': fields.selection(
            TYPE_TECHNIQUE,
            'Тип техники',
            required=True,
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', readonly=True),
        'department_id': fields.many2one('hr.department', 'Направление', readonly=True),
        'date_of_issue': fields.date('Дата выдачи', readonly=True),
        'date_of_purchase': fields.date(
            'Дата закупки',
            required=True,
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }),
        'cash': fields.float(
            'Стоимость',
            required=True,
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }),
        'cash_ye': fields.function(
            _get_rate,
            method=True,
            store=True,
            string='Стоимость $',
            type='float',
            digits=(12, 4),
            multi='rate',
            readonly=True,
        ),
        'rate': fields.function(
            _get_rate,
            method=True,
            string='Курс',
            type='float',
            digits=(12, 4),
            multi='rate',
            readonly=True,
        ),
        'currency_id': fields.many2one(
            'res.currency',
            'Валюта',
            required=True,
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }),
        'serial_number': fields.char(
            'Серийный номер',
            size=256,
            required=True,
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }),
        'inventory_number': fields.char(
            'Инвентарный номер',
            size=256,
            required=True,
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }),
        'cause_of_repair': fields.text(
            'Причина ремонта',
            states={
                'cancellation': [('readonly', True)],
                'on_cancellation': [('readonly', True)],
                'repair': [('readonly', True)],
            }),
        'venue_repair': fields.text(
            'Место проведения ремонта',
            states={
                'cancellation': [('readonly', True)],
                'on_cancellation': [('readonly', True)],
                'repair': [('readonly', True)],
            }),
        'reason_for_cancellation': fields.text(
            'Причина списания',
            states={
                'cancellation': [('readonly', True)],
                'on_cancellation': [('readonly', True)],
            }),
        'cancellation_act_number': fields.char(
            'Номер акта о списании',
            size=256,
            states={
                'cancellation': [('readonly', True)],
                'on_cancellation': [('readonly', True)],
            }),

        'history_ids': fields.one2many(
            'hr.technique.history',
            'technique_id',
            'История',
            readonly=True),
        'history_repair_ids': fields.one2many(
            'hr.technique.history.repair',
            'technique_id',
            'История ремонта',
            readonly=True),
        'comment_ids': fields.one2many(
            'hr.technique.comment',
            'technique_id',
            'Комментарии',
            states={
                'cancellation': [('readonly', True)],
                'on_cancellation': [('readonly', True)],
            }),
        'cancellation_employee_send_ids': fields.many2many(
            'hr.employee',
            'technique_employee_cancellation_rel',
            'technique_id',
            'employee_id',
            string='Комиссия по списанию',
            states={
                'cancellation': [('readonly', True)],
            }
        ),
        'cancellation_employee_ids': fields.one2many(
            'hr.technique.cancellation',
            'technique_id',
            'Комиссия по списанию',
            states={
                'cancellation': [('readonly', True)],
            }
        ),
        'stock': fields.selection(
            (
                ('upsale', 'UpSale'),
                ('ink', 'Inksystem')
            ), 'Склад',
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }),
        'account_id': fields.many2one(
            'account.account',
            'Состоит на балансе компании',
            domain=[('type', '!=', 'closed')],
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }
        ),
        'no_account': fields.boolean(
            'Нигде',
            readonly=True,
            states={
                'storage': [('readonly', False)],
            }
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Согласование',
            type='boolean',
            invisible=True
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='админы',
            type='boolean',
            invisible=True
        ),
    }

    _defaults = {
        'state': 'storage',
    }

    def save(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context.get('state'):
            return self.write(cr, uid, ids, {'state': context['state']})
        return False

    @notify.msg_send(_name)
    def write(self, cr, user, ids, vals, context=None):
        errors = []
        for record in self.read(cr, user, ids, []):
            action = ''
            state = record['state']
            next_state = vals.get('state')

            if vals.get('employee_id'):
                new_employee = self.pool.get('hr.employee').read(cr, user, vals['employee_id'], ['name'])
                if next_state == 'issued':
                    if record['employee_id']:
                        if record['employee_id'][0] != new_employee['id']:
                            action = u'Выдано: {old} -> {new}'.format(old=record['employee_id'][1], new=new_employee['name'])
                    else:
                        action = u'Выдано: {new}'.format(new=new_employee['name'],)
                if next_state == 'reserve':
                    if not (record['employee_id'] and record['employee_id'][0] == new_employee['id']):
                        action = u'Резерв: {new}'.format(new=new_employee['name'],)

            if next_state in ('storage', 'on_cancellation', 'cancellation'):
                vals['employee_id'] = None
                vals['department_id'] = None

            if next_state != 'issued':
                vals['date_of_issue'] = None

            if next_state and state != next_state and not action:
                action = 'Перевел: {old} -> {new}'.format(old=dict(STATES)[state], new=dict(STATES)[next_state])

            if next_state == 'repair':
                if not vals.get('cause_of_repair') and not record['cause_of_repair']:
                    errors.append('Необходимо заполнить причину ремонта.')
                if not vals.get('venue_repair') and not record['venue_repair']:
                    errors.append('Необходимо заполнить место проведения ремонта.')

            if next_state == 'on_cancellation':
                if not vals.get('reason_for_cancellation') and not record['reason_for_cancellation']:
                    errors.append('Необходимо заполнить причину списания.')
                if not vals.get('cancellation_act_number') and not record['cancellation_act_number']:
                    errors.append('Необходимо заполнить номер акта списания.')
                if not vals.get('cancellation_employee_send_ids') and not record['cancellation_employee_send_ids']:
                    errors.append('Необходимо выбрать людей в комиссию по списанию.')

            if errors:
                raise osv.except_osv('Учет техники', ' '.join(errors))

            if action:
                vals['history_ids'] = [(0, 0, {'name': action})]

                if state == 'repair' and next_state != state:
                    vals['history_repair_ids'] = [(0, 0, {'name': record['venue_repair'], 'cause_of_repair': record['cause_of_repair']})]
                    vals['venue_repair'] = ''
                    vals['cause_of_repair'] = ''

        return super(HrTechnique, self).write(cr, user, ids, vals, context)


HrTechnique()


class HrTechniqueHistory(Model):
    _name = 'hr.technique.history'
    _description = u'Учет техники - История'

    _columns = {
        'create_uid': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.char('Действие', size=256),
        'state': fields.char('Этап', size=256),
        'employee_id': fields.integer('Сотрудник'),
        'technique_id': fields.many2one('hr.technique', 'Техника'),
    }
HrTechniqueHistory()


class HrTechniqueHistoryRepair(Model):
    _name = 'hr.technique.history.repair'
    _description = u'Учет техники - История ремонта'

    _columns = {
        'create_uid': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.text('Место проведения ремонта'),
        'cause_of_repair': fields.text('Причина ремонта'),
        'technique_id': fields.many2one('hr.technique', 'Техника'),
    }
HrTechniqueHistoryRepair()


class HrTechniqueComment(Model):
    _name = 'hr.technique.comment'
    _description = u'Учет техники - Комментарии'

    _columns = {
        'create_uid': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.text('Комментарий'),
        'technique_id': fields.many2one('hr.technique', 'Техника'),
    }
HrTechniqueComment()


class HrTechniqueCancellation(Model):
    _name = 'hr.technique.cancellation'
    _description = u'Учет техники - Комиссия по списанию'
    _rec_name = 'employee_id'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.browse(cr, uid, ids, context):
            access = str()

            if data.employee_id and data.employee_id.user_id.id == uid:
                access += 'r'

            val = False
            letter = name[6]

            if letter in access or uid == 1:
                val = True
            res[data.id] = val
        return res

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник'),
        'date_agree': fields.date('Дата подтверждения'),
        'agree': fields.boolean('Подтверждение'),
        'technique_id': fields.many2one('hr.technique', 'Техника'),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Согласование',
            type='boolean',
            invisible=True
        ),
    }

    def write(self, cr, user, ids, vals, context=None):
        flag = super(HrTechniqueCancellation, self).write(cr, user, ids, vals, context)
        for record in self.read(cr, 1, ids, ['technique_id']):
            cancel_ids = self.search(cr, 1, [('technique_id', '=', record['technique_id'][0])])
            if cancel_ids and flag and set(i['agree'] for i in self.read(cr, 1, cancel_ids, ['agree'])) == set([True]):
                self.pool.get('hr.technique').write(cr, 1, [record['technique_id'][0]], {'state': 'cancellation'})
        return flag

    def save(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'agree': True, 'date_agree': datetime.date.today().strftime("%d/%m/%y")})
HrTechniqueCancellation()


class HrEmployee(Model):
    _inherit = 'hr.employee'

    _columns = {
        'technique_ids': fields.one2many(
            'hr.technique',
            'employee_id',
            'Техника',
            readonly=True,
            domain=[('state', '=', 'issued')]
        )
    }