# -*- coding: utf-8 -*-
import sys
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify

URL_PREFIX = '/openerp/form/save_binary_data/'


class storage_files(Model):
    _name = "storage.files"
    _rec_name = 'path'

    def _get_url(self, cr, uid, ids, name, arg, context):
        result = {}
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.name and not obj.is_folder:
               url = '/?_terp_field=data&_terp_model=storage.files&_terp_id='+str(obj.id)
               result[obj.id] = URL_PREFIX + obj.name.replace('\\', '/').split('/')[-1] + url
        return result

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        values['sendto_all'] = False
        return super(storage_files, self).write(cr, uid, ids, values, context)

    def _get_path(self, cr, uid, ids, field_name, arg, context):
        result = {}
        path = ''
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.parent_id:
                path = '/'.join((obj.parent_id.path, obj.name or ''))
            else:
                path = '/' + obj.name
            result[obj.id] = path
        return result

    _columns = {
        'user_id':  fields.many2one('res.users', 'Автор документа', select=True),
        'create_date': fields.datetime('Дата', readonly=True, select=True),

        'name': fields.char('Имя файла', size=64, select=True),
        'type': fields.char('Тип файла', size=6, select=True),
        'parent_id': fields.many2one('storage.files', string='Категория'),
        'is_folder': fields.boolean(string='Это папка'),
        'sendto_all': fields.boolean(string='Отправлять уведомления'),
        'url': fields.function(
            _get_url,
            type='char',
            method=True,
            store=True,
            size=255,
            string='Ссылка на файл'),
        'comment': fields.text('Коментарии'),
        'data': fields.binary('Выберите Файл'),
        'place_type': fields.selection(
            [
                ('binary', 'Файл'),
                ('web', 'Ссылка'),
            ], 'Разместить как'),
        'path': fields.function(
            _get_path,
            type='text',
            method=True,
            store=True,
            string='Полный путь'
        ),
        'web_url': fields.char('Ссылка', size=255),

        'responsible_user': fields.many2many(
            'res.users',
            'res_user_storage_docs_rel',
            'doc_id',
            'usr_id',
            string='Доступно'),
        'groups_user': fields.many2many(
            'storage.groups',
            'res_user_storage_docs_groups_rel',
            'doc_id',
            'gru_id',
            string='Группы доступа'
        ),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'place_type': lambda self, cr, uid, context: context.get('place_type', False),
        'is_folder': lambda self, cr, uid, context: context.get('is_folder', False),
        'sendto_all': True,
    }

    def onchange_path(self, cr, uid, ids, name, context=None):
        if name:
            name = name.replace('\\', '/').split('/')[-1]
            name = name.replace(' ', '_')
            type_file = name.split('.')[-1]
            return {'value': {'name': name, 'type': type_file}}
        return {'value': {}}

    def onchange_weburl(self, cr, uid, ids, web_url, context=None):
        if web_url:
            return {'value': {'type': 'url'}}
        return {'value': {}}

    def _check_file(self, cr, uid, ids, context=None):
        for field in self.browse(cr, uid, ids):
            if not field.data and not field.web_url and not field.is_folder:
                return False
        return True

    def _check_size(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            if field.data and not field.web_url and (sys.getsizeof(field.data) / 1024) > (30 * 1024):
                return False
        return True

    _constraints = [
        (_check_file, 'Необходимо вложить файл', ['name']),
        (_check_size, 'Файл больше 30Мб', ['data']),
    ]
    _order = 'path'

    def get_data(self, cr, uid, ids, context=None):
        field = self.browse(cr, uid, ids[0])
        if field.data:
            return field.data
        return False
storage_files()
