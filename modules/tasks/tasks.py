# -*- coding: utf-8 -*-
import logging
import netsvc
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify


wf_service = netsvc.LocalService("workflow")
_logger = logging.getLogger(__name__)


class Tasks(Model):
    _name = 'tasks'
    _description = u"Задания"
    _order = "create_date desc, name"
    _log_create = True

    states = (
        ('draft', 'Черновик'),
        ('cancel', 'Отмена'),
        ('agr_responsible', 'Согласование с ответственным'),
        ('rw_author', 'На доработке автором'),
        ('agr_performer', 'Согласование с исполнителем'),
        ('rw_responsible', 'На доработке ответственным'),
        ('inwork', 'В работе'),
        ('app_responsible', 'Утверждение ответственным'),
        ('rw_app_resp', 'На доработкe (утверждение остветсвенным)'),
        ('app_author', 'Утверждение автором'),
        ('rw_app_author', 'На доработкe (утверждение автором)'),
        ('done', 'Завершено'),
    )

    def get_state(self, state):
        return [item for item in self.states if item[0] == state][0]

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        if ids:
            data_ids = self.browse(cr, uid, ids, context)

            for data in data_ids:
                access = str()

                #  Автор
                if data.user_id.id == uid:
                    access += 'a'

                #  Ответственный
                if data.responsible_id.id == uid:
                    access += 'r'

                #  Исполнитель
                if data.performer_id.id == uid:
                    access += 'p'

                #  Руководитель ответственного
                if data.manager_id.id == uid:
                    access += 'm'

                #  Руководитель исполнителя
                if data.executive_id.id == uid:
                    access += 'e'

                val = False
                letter = name[6]
                if letter in access:
                    val = True

                res[data.id] = val
        return res

    def get_manager(self, cr, uid, id, context=None):
        employee_id = self.pool.get('hr.employee').search(cr, 1, [('user_id', '=', id)], context)
        manager_id = None
        if employee_id:
            employee_data = self.pool.get('hr.employee').browse(cr, 1, employee_id[0], context)
            if employee_data.parent_id.user_id:
                manager_id = employee_data.parent_id.user_id.id
        return manager_id

    def change_responsible(self, cr, uid, ids, responsible_id, user_id):
        v = {}
        hr_pool = self.pool.get('hr.employee')
        if responsible_id and responsible_id == user_id:
            v['check_r'] = True
            v['performer_id'] = responsible_id
            v['check_p'] = True
            v['executive_id'] = self.get_manager(cr, uid, responsible_id)
        else:
            v['check_r'] = False
            v['performer_id'] = None
            v['check_p'] = False

        v['manager_id'] = self.get_manager(cr, 1, responsible_id)
        return {'value': v}

    def copy(self, cr, uid, id, default=None, context=None):
        default['user_id'] = uid
        default['responsible_id'] = ''
        default['history_ids'] = None

        return super(Tasks, self).copy(cr, uid, id, default, context)

    def create(self, cr, uid, values, context=None):
        rid = super(Tasks, self).create(cr, uid, values, context)
        if values.get('responsible_id', False):
            if uid == values.get('responsible_id', False):
                signal = 'act_d_i'
            else:
                signal = 'act_d_ar'
            wf_service.trg_validate(uid, self._name, rid, signal, cr)
        return rid

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        """
            Проверки:
                1. Защита от бага перетаскивания задания на календаре
                2. Запрет постановки заданий задним число.
                    Нельзя constraint, необходимо учитывать только переход
                    с черновика
        """
        data = self.browse(cr, uid, ids)[0]

        next_state = values.get('state', False)
        state = data.state

        author = values.get('user_id', False) or data.user_id.id
        responsible = values.get('responsible_id', False) or data.responsible_id.id
        performer = values.get('performer_id', False) or data.performer_id.id

        if responsible:
            values['manager_id'] = self.get_manager(cr, uid, responsible)

        if author == responsible and not performer:
            performer = author
            values['performer_id'] = performer

        if performer:
            values['executive_id'] = self.get_manager(cr, uid, performer)

        error = ''
        if next_state and next_state != state:
            if next_state == 'inwork':
                if not values.get('start_date', False) and not data.start_date:
                    error += ' Необходимо ввести дату начала задания;'
                if not values.get('end_date', False) and not data.end_date:
                    error += ' Необходимо ввести дату окончания задания;'

            if error:
                raise osv.except_osv("Задания", error)

            values.update({'history_ids': [(0, 0, {
                'usr_id': uid,
                'state': self.get_state(next_state)[1]
            })]})

        for attachment in values.get('attachment_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'tasks'

        return super(Tasks, self).write(cr, uid, ids, values, context)

    _columns = {
        'state': fields.selection(states, 'статус задачи', size=20),
        'name': fields.char('Тема задания', size=256,
                            help='Назначение поля: данное поле позволяет просмотреть или задать тему для заявки. При создании новой заявки - это поле обязательно к заполнению. На этапе "Черновик" данное поле можно редактировать. На остальных этапах данное поле можно только просматривать.'),

        #  Участники процесса
        'user_id': fields.many2one('res.users', 'Автор', readonly=True, help=''),
        'responsible_id': fields.many2one('res.users', 'Ответственный', options={"quick_create": False},
                                          help='Назначение поля: в данном поле отображается ответственный за выполнение заявки. На этапе создания заявки это поле заполняется автоматически и указывается автор заявки. В случае, если автор и ответственный - не одно лицо, то ответственное лицо выбирается из ниспадающего списка. На этапе "Черновик" в данном поле можно поменять ответственного. На остальных этапах данное поле можно только просматривать.'),
        'performer_id': fields.many2one('res.users', 'Исполнитель',
                                        help='При создании новой заявки - это поле либо заполняется автоматически либо позволяет задать исполнителя  из ниспадающего списка (при переводе заявки на этап "Согласование с исполнителем"). На этапе "Черновик" в данном поле можно поменять исполнителя (если исполнитель и ответственный - ни одно лицо). На остальных этапах данное поле можно только просматривать.'),
        'manager_id': fields.many2one('res.users', 'Руководитель ответственного', invisible=True),
        'executive_id': fields.many2one('res.users', 'Руководитель исполнителя', invisible=True),

        'create_date': fields.datetime('Дата создания', readonly=True,
                                       help='Назначение поля: данное поле позволяет просмотреть дату создания заявки. При создании новой заявки - это поле заполняется автоматически. Редактировать данное поле нельзя.'),
        'start_date': fields.datetime('Дата начала',
                                      help='Назначение поля: данное поле позволяет задать дату начала выполнения заявки. Также данное поле обязательно к заполнению при переводе заявки на этап "В работу". На этапе "В работу" данное поле можно только просматривать, на остальных этапах его можно редактировать.'),
        'end_date': fields.datetime('Дата окончания',
                                    help='Назначение поля: данное поле позволяет задать конечную дату выполнения заявки. Данное поле обязательно к заполнению при переводе заявки на этап "В работу". На этапе "В работу" данное поле можно только просматривать, на остальных этапах его можно редактировать.'),

        'description': fields.text('Описание',
                                   help='Назначение поля: данное поле позволяет описать суть заявки. При создании новой заявки - это поле обязательно к заполнению. На этапе "Черновик" и "На доработке автором" данное поле можно редактировать. На остальных этапах данное поле можно только просматривать.'),

        'files_ids': fields.one2many('attach.files', 'obj_id', 'Вложения', help=''),
        'attachment_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Вложения',
            domain=[('res_model', '=', 'tasks')],
            context={'res_model': 'tasks'},
            help='Назначение поля: в данном поле можно прикрепить необходимые материалы для выполнения заявки. Данное поле - необязательно к заполнению.'
        ),
        'comment_ids': fields.one2many('tasks.comments', 'task_id', 'Комментарии',
                                       help='Назначение поля: в данном поле можно задать нужный комментарий при необходимости. Данное поле можно редактировать на любом этапе, кроме "Черновик", "Отмена" и "Завершено". В случае перевода заявки на доработку, данное поле является обязательным к заполнению.'),
        'history_ids': fields.one2many('tasks.history', 'task_id', 'История переходов',
                                       help='Назначение поля: в данном поле отображается история этапов выполнения заявки. Это поле нельзя редактировать, оно заполняется автоматически.'),
        'start_term': fields.selection(
            [
                ('10min', 'за 10 минут'),
                ('30min', 'за 30 минут'),
                ('1hour', 'за 1 час'),
                ('3hour', 'за 3 часа'),
                ('1day', 'за 1 день')
            ], 'Отправлять напоминание',
            help='Назначение поля: данное поле позволяет задать напоминание по заявке. При создании новой заявки - это поле не является обязательным к заполнению. На этапе "Черновик" и "На доработке автором" данное поле можно редактировать. На остальных этапах данное поле можно только просматривать.'),

        #  Проверки сообщений
        'notify': fields.boolean('Уведомление о начале выполнения', help=''),
        'deadline': fields.boolean('Уведомление о просроченом задании', help=''),

        #  Права
        'check_a': fields.function(
            _check_access,
            method=True,
            string='Проверка на автора',
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
        'check_p': fields.function(
            _check_access,
            method=True,
            string='Проверка на исполнителя',
            type='boolean',
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string='Проверка на руководитель ответственного',
            type='boolean',
            invisible=True
        ),
        'check_e': fields.function(
            _check_access,
            method=True,
            string='Проверка на руководителя исполнителя',
            type='boolean',
            invisible=True
        ),
    }

    _defaults = {
        'user_id': lambda s, c, u, cnt: u,
        'responsible_id': lambda s, c, u, cnt: u,
        'state': 'draft',
        'check_a': True,
    }

    def workflow_setter(self, cr, uid, ids, state='draft'):
        return self.write(cr, uid, ids, {'state': state})

    def check_notify(self, cr, uid, context=None):
        print "Check CRON"
Tasks()


class TaskComments(Model):
    _name = 'tasks.comments'
    _description = u"Задания: Комментарии"
    _order = "create_date desc"

    _columns = {
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.text('Комментарий'),
        'task_id': fields.many2one('tasks', 'Task', invisible=True),
    }

    _defaults = {
        'usr_id': lambda s, c, u, cnt: u,
    }
TaskComments()


class TaskHistory(Model):
    _name = 'tasks.history'
    _description = u'Task - История переходов'
    _log_create = True
    _order = "create_date desc"
    _rec_name = 'state'

    _columns = {
        'usr_id': fields.many2one('res.users', 'Перевел'),
        'state': fields.char('На этап', size=65),
        'create_date': fields.datetime('Дата', readonly=True),
        'task_id': fields.many2one('tasks', 'Task', invisible=True),
    }

    _defaults = {
        'usr_id': lambda s, c, u, cnt: u,
    }
TaskHistory()
