# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from osv import osv, orm, fields
from notify import notify


class company_infonote(osv.osv):
    _name = 'company.info.note'
    _description = 'Part of Company_Documents module: Information notes'
    _order = "create_date desc"

    states = {'draft': u'Черновик', 'waiting': u'На согласовании', 'rework': u'На доработке',
              'published': u'Опубликовано', 'cancel': u'Отменено'}

    workflow_name = u'Бизнес-процесс Информационные записки'
    _msg_fields = ['id', 'name']

    def check_manager(self, cr, uid, ids, context=None):
        """
            Проверка роли менеджера
            Используются при переходах в бизнес-процессе
        """
        data = self.browse(cr, uid, ids[0], context=None)
        if data.department_manager.user_id.id == uid:
            return True
        return False

    def check_author(self, cr, uid, ids, context=None):
        """
            Проверка роли автора,
            Используется при переходах  в бизнес-процессе
        """
        data = self.browse(cr, uid, ids[0], context=None)
        if data.author.user_id.id == uid:
            return True
        return False

    def compile_message(self, cr, uid, message_text, object_data):
        replace_dict = [(u"АВТОР", object_data.author.name),
                        (u"ДАТА СОЗДАНИЯ", object_data.create_date),
                        (u"ЭТАП", self.states[object_data.state]),
                        (u"ТЕМА", object_data.name),
                        (u"НОМЕР", unicode(object_data.id)),
                        ]
        for item in replace_dict:
            message_text = message_text.replace(item[0], item[1])
        return message_text

    def default_department_manager(self, cr, uid, context=None):
        employee_id = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        data = self.pool.get('hr.employee').browse(cr, uid, employee_id[0])
        if data.manager == True:
            return employee_id[0]
        if data.department_id:
            return data.department_id.manager_id.id
        return False

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        if ids:
            data = self.browse(cr, uid, ids[0], context)
            access = str()
            if data.author.user_id.id == uid:
                access = 'author'
            elif data.department_manager.user_id.id == uid:
                access = 'manager'
            res[data.id] = access
        return res

    _columns = {
        'create_date': fields.datetime(u'Дата создания', readonly=True),
        'send_to': fields.many2many('res.users', 'employee_info_relation', 'info_id', 'user_id', string=u'Кому'),
        'author': fields.many2one('hr.employee', u'От кого', readonly=True),
        'department_manager': fields.many2one('hr.employee', u'Руководитель направления', invisible=True),
        'name': fields.char(u'Тема', size=255, required=True),
        'content': fields.text(u'Содержание', required=True),
        'redo_comment': fields.text(u'Комментарий по доработке'),
        'state': fields.selection([('draft', u'Черновик'),
                                   ('waiting', u'На согласовании'),
                                   ('rework', u'На доработке'),
                                   ('published', u'Опубликовано'),
                                   ('cancel', u'Отменено')], u'Этап', readonly=True),
        'access': fields.function(_check_access, method=True, string=u"Права", type="char", invisible=True),
        }

    _defaults = {
        'state': 'draft',
        'author': lambda self, cr, uid, context: self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])[
            0],
        'department_manager': lambda self, cr, uid, context: self.default_department_manager(cr, uid, context)
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

    def action_published(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'published'}, context)
        return [data.send_to.user_id.id]

    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context)

    @notify.msg_send(_name, u'Бизнес-процесс Информационные записки')
    def write(self, cr, uid, ids, values, context=None):
        return super(company_infonote, self).write(cr, uid, ids, values, context)

    def _check_redo_comment(self, cr, uid, ids, context=None):
        """
            При отправке на доработку должны быть заполнены поля комментариев
        """
        data = self.read(cr, uid, ids[0], ['state', 'redo_comment'], context)
        if data.get('state') == 'rework' and not data.get('redo_comment'):
            return False
        return True

    _constraints = [
        (_check_redo_comment,
         'Заполните поле комментарий',
         [u'Комментарий на доработку']),
    ]

company_infonote()