# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta
import pytz

from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model


STATES = (
    ('draft', 'Черновик'),
    ('completion', 'На доработке инициатором'),
    ('decision', 'Принятие решения'),
    ('in_pipeline', 'В работе'),
    ('completion_performer', 'На доработке исполнителем'),
    ('approval', 'Сдано на утверждение'),
    ('accepted', 'Принято инициатором'),
    ('cancel', 'Отмена'),
)


def format_date_tz(date, tz=None):
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
    if tz is None:
        tz = pytz.timezone(tools.detect_server_timezone())
    f = tools.DEFAULT_SERVER_DATETIME_FORMAT
    return tools.server_to_local_timestamp(date, f, f, tz)


def parse_timedelta(timedelta_str):
    if 'day' in timedelta_str:
        timedelta_str.replace(' days, ', ':')
        timedelta_str.replace(' day, ', ':')
    return timedelta_str


def str_to_seconds(timedelta_str):
    total_seconds = 0
    timedelta_list = timedelta_str.split(':')
    total_seconds += int(timedelta_list[-1])
    total_seconds += int(timedelta_list[-2]) * 60
    total_seconds += int(timedelta_list[-3]) * 60 * 60
    if len(timedelta_list) == 4:
        total_seconds += int(timedelta_list[-3]) * 60 * 60 * 24

    return total_seconds


class Incidents(Model):
    _name = 'ink.incidents'
    _description = u'Реестр инцидентов INK'

    _order = "id desc"

    def change_person(self, cr, user, ids, person_id, type='author', context=None):
        department_str = '{0}_department_id'.format(type)
        parent_str = '{0}_parent_id'.format(type)
        for person in self.pool.get('hr.employee').read(cr, user, [person_id], ['department_id', 'parent_id'], context):
            department = 0
            parent = 0
            if person['department_id']:
                department = person['department_id'][0]
            if person['parent_id']:
                parent = person['parent_id'][0]
                
            return {'value':  {department_str: department, parent_str: parent}}

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        employee_pool = self.pool.get('hr.employee')
        employee = employee_pool.get_employee(cr, uid, uid)
        res = {}
        for record in self.read(cr, uid, ids, ['author_id', 'author_parent_id', 'performer_id', 'performer_parent_id']):
            access = str()
            #  Автор
            if (record['author_id'] and record['author_id'][0] == employee.id) \
               or (record['author_parent_id'] and record['author_parent_id'][0] == employee.id):
                access += 'a'

            #  Ответственный
            if (record['performer_id'] and record['performer_id'][0] == employee.id) \
               or (record['performer_parent_id'] and record['performer_parent_id'][0] == employee.id):
                access += 'p'

            val = False
            letter = name[6]
            if letter in access:
                val = True

            res[record['id']] = val
        return res

    _columns = {
        'id': fields.integer('№', size=11, select=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'author_id': fields.many2one('hr.employee', 'Инициатор', readonly=True),
        'author_department_id': fields.related(
            'author_id',
            'department_id',
            relation='hr.department',
            type='many2one',
            string='Направление инициатора',
            store=True
        ),
        'author_parent_id': fields.related(
            'author_id',
            'parent_id',
            relation='hr.employee',
            type='many2one',
            string='Руководитель инициатора',
            store=True
        ),

        'name': fields.char(
            'Тема инцидента',
            size=250,
            readonly=True,
            states={
                'draft': [('readonly', False), ('required', True)],
                'completion': [('readonly', False), ('required', True)]
            }),
        'description': fields.text(
            'Описание инцидента',
            readonly=True,
            states={
                'draft': [('readonly', False), ('required', True)],
                'completion': [('readonly', False), ('required', True)]
            }
        ),
        'type': fields.selection(
            (
                ('fail', 'Сбой в работе'),
                ('issues', 'Текущие вопросы'),
            ), 'Тип инцидента',
            readonly=True,
            states={
                'draft': [('readonly', False), ('required', True)],
                'completion': [('readonly', False), ('required', True)]
            }
        ),
        'document_type': fields.selection(
            (
                ('cash-memo', 'Товарный чек'),
                ('invoice', 'Счет на оплату'),
                ('mail', 'Почтовая отправка'),
                ('receipt for repairs', 'Квитанция о ремонте'),
                ('bill', 'Товарная (расходная) накладная'),
                ('movement', 'Накладная на перемещение'),
            ), 'Тип документа',
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'completion': [('readonly', False)]
            }
        ),
        'document_number': fields.char(
            '№ документа',
            size=250,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'completion': [('readonly', False)]
            }),

        'performer_id': fields.many2one(
            'hr.employee',
            'Ответственный исполнитель',
            readonly=True,
            states={
                'draft': [('readonly', False), ('required', True)],
                'completion': [('readonly', False), ('required', True)]
            }
        ),
        'performer_department_id': fields.related(
            'performer_id',
            'department_id',
            relation='hr.department',
            type='many2one',
            string='Направление исполнителя',
            store=True
        ),
        'performer_parent_id': fields.related(
            'performer_id',
            'parent_id',
            relation='hr.employee',
            type='many2one',
            string='Руководитель исполнителя',
            store=True
        ),

        'deadline_date': fields.datetime(
            'Срок исполнения',
            readonly=True,
            states={
                'draft': [('readonly', False), ('required', True)],
                'completion': [('readonly', False), ('required', True)]
            }),

        'time_over_decision': fields.char('Время превышения принятия решения', size=20, readonly=True),
        'time_over_waiting_initiator': fields.char('Время превышения ожидания ответа инициатора', size=20, readonly=True),
        'time_over_deadlines': fields.char('Время превышения сроков выполнения', size=20, readonly=True),

        'state': fields.selection(STATES, 'Статус', size=100, readonly=True),
        'history_ids': fields.one2many('ink.incidents.history', 'incident_id', 'История переходов', readonly=True),

        'fallback': fields.text(
            'Обратная связь от исполнителя',
        ),
        'comment_completion': fields.text(
            'Комментарий по доработке (от исполнителя)',
        ),
        'comment_approval': fields.text(
            'Комментарий по доработке (от инициатора)',
        ),
        'comment_ids': fields.one2many('ink.incidents.comment', 'incident_id', 'Инцидент', readonly=False),

        #  Права
        'check_a': fields.function(
            _check_access,
            method=True,
            string='Проверка на инициатора',
            type='boolean',
            invisible=True
        ),
        'check_p': fields.function(
            _check_access,
            method=True,
            string='Проверка на ответственного',
            type='boolean',
            invisible=True
        ),
    }

    _defaults = {
        'author_id': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).id,
        'state': 'draft',
        'check_a': True,
    }

    def write(self, cr, user, ids, vals, context=None):
        history_pool = self.pool.get('ink.incidents.history')
        next_state = vals.get('state', False)
        check_date = datetime.now(pytz.utc)

        for record in self.browse(cr, user, ids, context):
            if next_state and next_state != record.state:
                if record.state == 'decision':
                    if record.history_ids:
                        new_delta_seconds = 0
                        state_date = datetime.strptime(record.history_ids[-1].create_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
                        delta = check_date - state_date

                        record_delta = 0
                        if record.time_over_decision:
                            record_delta = str_to_seconds(record.time_over_decision)

                        if delta.seconds > 3600:
                            new_delta_seconds = record_delta + delta.seconds + delta.days*3600*24 - 3600
                            vals['time_over_decision'] = parse_timedelta(str(timedelta(seconds=new_delta_seconds)))

                if record.state == 'completion' and next_state == 'decision':
                    if record.history_ids:
                        new_delta_seconds = 0
                        record_delta = 0
                        state_date = datetime.strptime(record.history_ids[-1].create_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
                        delta = check_date - state_date

                        if record.time_over_waiting_initiator:
                            record_delta = str_to_seconds(record.time_over_waiting_initiator)

                        if delta.seconds > 3600:
                            new_delta_seconds = record_delta + delta.seconds + delta.days*3600*24 - 3600
                            vals['time_over_waiting_initiator'] = parse_timedelta(str(timedelta(seconds=new_delta_seconds)))

                if next_state == 'accepted':
                    new_delta_seconds = 0
                    record_delta = 0
                    state_date_deadline = datetime.strptime(record.deadline_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
                    if record.time_over_deadlines:
                        record_delta = str_to_seconds(record.time_over_deadlines)

                    delta = check_date - state_date_deadline
                    if delta.days >= 0:
                        new_delta_seconds = record_delta + delta.seconds + delta.days*3600*24
                        vals['time_over_deadlines'] = parse_timedelta(str(timedelta(seconds=new_delta_seconds)))

                if record.state == 'in_pipeline' and next_state == 'approval' and not record['fallback'] and not vals.get('fallback'):
                    raise osv.except_osv('', 'Нужно заполнить "Обратная связь от исполнителя"')

                if next_state == 'completion' and not record['comment_completion'] and not vals.get('comment_completion'):
                    raise osv.except_osv('', 'Нужно заполнить "Комментарий по доработке  (от исполнителя)"')
                if next_state == 'completion_performer' and not record['comment_approval'] and not vals.get('comment_approval'):
                    raise osv.except_osv('', 'Нужно заполнить "Комментарий по доработке  (от инициатора)"')

                vals.update({'history_ids': [(0, 0, {'name': next_state})]})

        return super(Incidents, self).write(cr, user, ids, vals, context)

    def add_note(self, cr, uid, ids, context=None):
        view_id = self.pool.get('ir.ui.view').search(
            cr,
            uid,
            [('name', 'like', 'ink.incidents.add.note.form1')]
        )
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ink.incidents.comment',
            'name': 'Комментарий',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': {
                'incident_id': ids[0],
            },
            'target': 'new',
            'nodestroy': True,
        }
Incidents()


class IncidentsHistory(Model):
    _name = 'ink.incidents.history'
    _description = u'Реестр инцидентов INK - История переводов'

    _columns = {
        'name': fields.selection(STATES, 'Статус', size=100, readonly=True),
        'create_date': fields.datetime('Дата и время перевода'),
        'create_uid': fields.many2one('res.users', 'Перевел'),
        'incident_id': fields.many2one('ink.incidents', 'Инцидент'),
    }
IncidentsHistory()


class IncidentsComment(Model):
    _name = 'ink.incidents.comment'
    _description = u'Реестр инцидентов INK - Комментарии'

    _columns = {
        'name': fields.text('Комментарий'),
        'create_date': fields.datetime('Дата и время создания'),
        'create_uid': fields.many2one('res.users', 'Автор'),
        'incident_id': fields.many2one('ink.incidents', 'Инцидент', invisible=True),
    }

    def action_add(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        incident = context.get('incident_id')

        for obj in self.browse(cr, uid, ids, context=context):
            self.write(
                cr,
                uid,
                obj.id,
                {
                    'name': obj.name,
                    'incident_id': incident
                })

        return {'type': 'ir.actions.act_window_close'}
IncidentsHistory()