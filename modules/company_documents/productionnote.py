# -*- coding: utf-8 -*-
from osv import osv, orm, fields
from datetime import datetime
from notify import notify
import pytz


class company_productionnote(osv.osv):
    _name = 'company.production.note'
    _description = 'Part of Company_Documents module: Production notes'
    _order = "create_date desc"

    states = {'draft': u'Черновик',
              'waiting': u'На согласовании',
              'rework': u'На доработке',
              'decision': u'Принятие решения',
              'closed': u'Закрыто принимающим решение',
              'inwork': u'Исполнение',
              'approval': u'Сдано на утверждение',
              'failed': u'Не выполнено',
              'init_accepted': u'Принято инициатором',
              'init_failed': u'Не принято инициатором',
              'cancel': u'Отменено', }

    workflow_name = u'Бизнес-процесс Проблемные записки'
    _msg_fields = ['id', 'name']

    def check_manager(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=None)
        if data.department_manager.user_id.id == uid:
            return True
        return False

    def check_author(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=None)
        if data.author.user_id.id == uid:
            return True
        return False

    def check_responsible(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=None)
        if data.responsible_employee.user_id.id == uid:
            return True
        return False

    def check_decision(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=None)
        if data.chief_officer.user_id.id == uid:
            return True
        return False

    def compile_message(self, cr, uid, message_text, object_data):
        replace_dict = [(u"АВТОР", object_data.author.name),
                        (u"ДАТА СОЗДАНИЯ", object_data.create_date),
                        (u"ЭТАП", self.states[object_data.state]),
                        (u"ТЕМА", object_data.name),
                        (u"НОМЕР", unicode(object_data.id)),
                        (u"ИСПОЛНИТЕЛЬ", object_data.responsible_employee.name),
                        (u"ПРИНИМАЮЩИЙ РЕШЕНИЯ", object_data.chief_officer.name),
                        (u"СРОК ИСПОЛНЕНИЯ", object_data.deadline),
                        ]

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if ids:
            data = self.browse(cr, uid, ids[0], context)
            access = str()
            if data.author.user_id.id == uid:
                access = 'author'
            elif data.department_manager.user_id.id == uid:
                access = 'manager'
            elif data.chief_officer.user_id.id == uid:
                access = 'decision'
            else:
                access = 'responsible'
            res[data.id] = access
        return res

    def check_deadline(self, cr, uid, context=None):
        dead_ids = self.search(cr, uid, [('state', '=', 'inwork')])
        current_date = datetime.now(pytz.utc)
        for dead_id in dead_ids:
            data = self.browse(cr, uid, dead_id, context)
            dead_date = datetime.strptime(data.deadline, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            if current_date > dead_date:
                message_data = self.get_message_controller_data(cr, uid, self.workflow_name, self.states[data.state],
                                                                'deadline')
                self.send_message(cr, uid, [dead_id], message_data, [data.chief_officer.user_id.id], context)
        return True

    _columns = {
        'create_date': fields.datetime(u'Дата создания', readonly=True),
        'author': fields.many2one('hr.employee', u'От кого', readonly=True),
        'department_manager': fields.many2one('hr.employee', u'Руководитель направления', invisible=True),
        'name': fields.char(u'Тема', size=255, required=True),
        'content': fields.text(u'Содержание', required=True),
        'redo_comment': fields.text(u'Комментарий по доработке'),
        'decision': fields.char(u'Принято решение', size=255),
        'accepted': fields.selection([('no', u'Нет'), ('yes', u'Да')], u'Принято к исполнению'),
        'comments': fields.text(u'Комментарии'),
        'responsible_employee': fields.many2one('hr.employee', u'Ответственный за исполнение'),
        'deadline': fields.datetime(u'Срок исполнения'),
        'completed': fields.selection([('no', u'Нет'), ('yes', u'Да')], u'Отметка об исполнении'),
        'init_comment': fields.text(u'Комментарий инициатора'),
        'resp_comment': fields.text(u'Комментарий овтетственного'),
        'state': fields.selection(zip(states.keys(), states.values()), u'Этап', readonly=True),
        'chief_officer': fields.many2one('hr.employee', u'Генеральный директор',
                                         domain=[('job_id.name', 'like', u'Генеральный')], required=True),
        'access': fields.function(_check_access, method=True, string=u"Права", type="char", invisible=True),
    }

    def action_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context)

    def action_waiting(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'waiting'}, context)
        return [data.department_manager.user_id.id]

    def action_rework(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'rework'}, context)
        return [data.author.user_id.id]

    def action_decision(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'decision'}, context)
        return [data.chief_officer.user_id.id]

    def action_closed(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'closed'}, context)
        return [data.author.user_id.id]

    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context)

    def action_inwork(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'inwork'}, context)
        return [data.responsible_employee.user_id.id]

    def action_failed(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'failed'}, context)
        return [data.chief_officer.user_id.id, data.author.user_id.id]

    def action_approval(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'approval'}, context)
        return [data.author.user_id.id]

    def action_init_failed(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'init_failed'}, context)
        return [data.chief_officer.user_id.id, data.responsible_employee.user_id.id]

    def action_init_accepted(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'init_accepted'}, context)
        return [data.chief_officer.user_id.id, data.responsible_employee.user_id.id]

    def default_department_manager(self, cr, uid, context=None):
        employee_id = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        data = self.pool.get('hr.employee').browse(cr, uid, employee_id[0])
        if data.manager:
            return employee_id[0]
        if data.department_id:
            return data.department_id.manager_id.id
        return False

    @notify.msg_send(_name, u'Бизнес-процесс Проблемные записки')
    def write(self, cr, uid, ids, values, context=None):
        return super(company_productionnote, self).write(cr, uid, ids, values, context)

    _defaults = {
        'state': 'draft',
        'author': lambda self, cr, uid, context: self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])[0],
        'department_manager': lambda self, cr, uid, context: self.default_department_manager(cr, uid, context)
    }

    def _check_redo_comment(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], ['state', 'redo_comment'], context)
        if data.get('state') == 'rework' and not data.get('redo_comment'):
            return False
        return True

    def _check_inwork(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], ['state', 'responsible_employee', 'decision'], context)
        if data.get('state') == 'inwork' and not data.get('responsible_employee') and not data.get('decision'):
            return False
        return True

    def _check_comments(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], ['state', 'comments'], context)
        if data.get('state') == 'closed' and not data.get('comments'):
            return False
        return True

    _constraints = [
        (_check_redo_comment,
         'Заполните поле комментарий',
         [u'Комментарий на доработку']),
        (_check_inwork,
         'Вы не заполнили поле сотрудник или решение по исполнению',
         [u'Ответственный сотрудник', u'Решение']),
        (_check_comments,
         'При закрытии записки, обязательно, укажите причину в комментариях',
         [u'Комментарии']),
    ]

company_productionnote()