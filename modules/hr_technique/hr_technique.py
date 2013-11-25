# coding=utf-8
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
    ('network', 'Сетевое оборудование')
)


class HrTechnique(Model):
    _name = 'hr.technique'
    _description = u'Учет техники'

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
        'cause_of_repair': fields.text('Причина ремонта'),
        'venue_repair': fields.text('Место проведения ремонта'),
        'reason_for_cancellation': fields.text('Причина списания'),
        'cancellation_act_number': fields.char('Номер акта о списании', size=256),

        'history_ids': fields.one2many('hr.technique.history', 'technique_id', 'История'),
        'comment_ids': fields.one2many('hr.technique.comment', 'technique_id', 'Комментарии'),
        'cancellation_employee_send_ids': fields.many2many(
            'hr.employee',
            'technique_employee_cancellation_rel',
            'technique_id',
            'employee_id',
            string='Комиссия по списанию',
        ),
        'cancellation_employee_ids': fields.one2many(
            'hr.technique.cancellation',
            'technique_id',
            'Комиссия по списанию'
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

            if next_state != 'issued':
                vals['date_of_issue'] = None

            if next_state and state != next_state and not action:
                action = 'Перевел: {old} -> {new}'.format(old=dict(STATES)[state], new=dict(STATES)[next_state])

            if action:
                vals['history_ids'] = [(0, 0, {'name': action})]

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

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник'),
        'date_agree': fields.date('Дата подтверждения'),
        'agree': fields.boolean('Подтверждение'),
        'technique_id': fields.many2one('hr.technique', 'Техника'),
    }
HrTechniqueCancellation()
