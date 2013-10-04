# -*- coding: utf-8 -*-
from notify import notify
from openerp.osv import fields
from openerp.osv.orm import Model


class company_disposal(Model):
    _name = 'company.disposal'
    _description = u'Распоряжения'
    _order = "create_date desc"

    states = {
        'draft': u'Черновик',
        'waiting': u'На утверждении',
        'rework': u'На доработке',
        'approved': u'Утверждено',
        'cancel': u'Отменено'
    }

    def check_author(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context)
        if data.author.user_id.id == uid:
            return True
        return False

    def check_chief(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=None)
        if data.chief_officer.user_id.id == uid:
            return True
        return False

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if ids:
            data = self.browse(cr, uid, ids[0], context)
            access = str()
            if data.author.user_id.id == uid:
                access = 'author'
            elif data.chief_officer.user_id.id == uid:
                access = 'chief'
            elif data.former.user_id == uid:
                access = 'former'
            res[data.id] = access
        return res

    _columns = {
        'create_date': fields.datetime(u'Дата создания', readonly=True),
        'send_to': fields.many2many(
            'res.users',
            'employee_disposal_relation',
            'disposal_id',
            'user_id',
            string=u'Кому'
        ),
        'sendto_all': fields.boolean(string='Отправлять уведомления'),
        'former': fields.many2one('hr.employee', u'Составитель', required=True),
        'author': fields.many2one('hr.employee', u'От кого', readonly=True),
        'name': fields.char(u'Тема', size=255, required=True),
        'content': fields.text(u'Содержание', required=True),
        'redo_comment': fields.text(u'Комментарий по доработке'),
        'chief_officer': fields.many2one('hr.employee', u'Утверждает', domain=[('job_id.name', 'like', u'Генеральный')],
                                         required=True),
        'state': fields.selection(zip(states.keys(), states.values()), u'Этап', readonly=True),
        'access': fields.function(_check_access, method=True, string=u"Права", type="char", invisible=True),
        'groups_user': fields.many2many('storage.groups', 'res_user_company_disposal_groups_rel', 'doc_id', 'gru_id',
                                        string='Группы доступа'),
    }

    _defaults = {
        'state': 'draft',
        'author': lambda self, cr, uid, context: self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])[0],
        'former': lambda self, cr, uid, context: self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])[0],
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        print values
        return super(company_disposal, self).write(cr, uid, ids, values, context)

    def _check_redo_comment(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], ['state', 'redo_comment'], context)
        if data.get('state') == 'rework' and not data.get('redo_comment'):
            return False
        return True

    _constraints = [
        (_check_redo_comment,
         'Заполните поле комментарий',
         [u'Комментарий на доработку']),
    ]

company_disposal()