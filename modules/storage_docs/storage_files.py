# -*- coding: utf-8 -*-
from osv import osv, fields
import sys
from notify import notify

URL_PREFIX = '/openerp/form/save_binary_data/'


class storage_files(osv.osv):
    _name = "storage.files"
    _rec_name = 'path'

    def _get_url(self, cr, uid, ids, name, arg, context):
        result = {}
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.name and not obj.is_folder:
               url = '/?_terp_field=data&_terp_model=storage.files&_terp_id='+str(obj.id)
               result[obj.id] = URL_PREFIX + obj.name.replace('\\', '/').split('/')[-1] + url
        return result

    def grant_access(self, cr, uid, ids, grant_access_users, comment=False, context=None):
        if grant_access_users:
            data = self.browse(cr,uid,ids)
            for obj in data:
                request = self.pool.get('res.request')
                message_text = u"Вам доступен документ «%s» загружен пользователем «%s»" % (obj.path, obj.user_id.name)
                if comment or obj.comment:
                    print "Comment: %s" % comment
                    try:
                        c = comment if comment else obj.comment
                        c = c.encode('utf-8')
                        message_text += " с комментарием: {0} ".format(c)
                    except:
                        pass
                #print message_text

                message = {
                        'body': message_text,
                        'name': unicode("Вам дали доступ на новый файл", "utf-8"),
                        'state': 'waiting',
                        'priorty': '1',
                        'act_from': uid,
                        'active': True,
                        'act_to': False,
                }

                for user in grant_access_users:
                    message['act_to'] = user
                    request.create(cr,uid,message)
        return True

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        '''
        data = self.read(cr, uid, ids,['responsible_user', 'groups_user', 'sendto_all'])
        if values.get('responsible_user') or values.get('groups_user') or data[0]['responsible_user'] or data[0]['groups_user']:
            if data[0]['sendto_all'] or values.get('sendto_all'):
                current_responsible = data[0]['responsible_user']
                current_groups_user = data[0]['groups_user']

                future_responsible = []
                future_groups_user = []
                grant_access_users = []
                grant_access_groups = []
                if values.get('responsible_user') or current_responsible:
                    future_responsible = values.get('responsible_user', [])
                    grant_access_users = future_responsible if future_responsible else current_responsible
                    #grant_access_users = list(set(future_responsible) + set(current_responsible))


                if values.get('groups_user') or current_groups_user:
                    gr_users = values.get('groups_user')[0][2] if values.get('groups_user') else []
                    #list_groups_user = list(set(gr_users) + set(current_groups_user))
                    list_groups_user = gr_users if gr_users else current_groups_user

                    data_groups_user = self.pool.get('storage.groups').read(cr, uid, list_groups_user,['users_group','is_all'])
                    if data_groups_user:
                       for val in data_groups_user:
                           if not val['is_all']:
                               future_groups_user = future_groups_user + val['users_group']
                           else:
                               future_groups_user = self.pool.get('res.users').search(cr, uid, [('active','=',True)])
                               break

                    grant_access_groups = list(set(future_groups_user))
                grant_access = list(set(grant_access_groups + grant_access_users))

                #print "GA: %s" % grant_access
                self.grant_access(cr, uid, ids, grant_access, values.get('comment', False))
        '''
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
