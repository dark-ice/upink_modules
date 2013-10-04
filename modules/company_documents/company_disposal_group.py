# coding=utf-8
from osv import osv
from osv import fields

class company_disposal_groups(osv.osv):
    _name = "company.disposal.groups"
    _columns = {
        'name': fields.char('Название группы', select=True, size=64),
        'users_group': fields.many2many('res.users', 'res_user_storage_groups_rel', 'gro_id', 'usr_id',
            string='Список пользователей', select=True),
        'comment': fields.text('Коментарии'),
        'is_all': fields.boolean('Добавить всех'),
        'user_id': fields.many2one('res.users', 'Автор группы', select=True),
        'create_date': fields.datetime('Дата', readonly=True, select=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

    def write(self, cr, uid, ids, values, context=None):
        if values.get('users_group'):
            data = self.read(cr, uid, ids, ['users_group', 'is_all'])
            doc_gr = self.pool.get('company.disposal').search(cr, uid,
                [('groups_user', 'in', ids[0]), ('sendto_all', '=', True)])

            grant_access_users = list(set(values.get('users_group')[0][2]) - set(data[0]['users_group']))
            if grant_access_users:
                self.pool.get('company.disposal').grant_access(cr, uid, doc_gr, grant_access_users)
        return super(osv.osv, self).write(cr, uid, ids, values, context=None)

company_disposal_groups()