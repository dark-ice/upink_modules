# -*- coding: utf-8 -*-

##############################################################################
#
#    Authors: Tverdokheb Sergey
#    Copyright (C) 2011 - 2012 by Upsale co, www.upsale.ru.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields


class storage_groups(osv.osv):
    _name = "storage.groups"

    #def write(self, cr, uid, ids, values, context=None):
    #    if values.get('users_group'):
    #        data = self.read(cr, uid, ids, ['users_group', 'is_all'])
    #        doc_gr = self.pool.get('storage.files').search(cr, uid, [('groups_user', 'in', ids[0]), ('sendto_all', '=', True)])
    #        #if values.get('is_all'):
    #            #grant_access_users = self.pool.get('res.users').search(cr, uid, [('active','=',True)])
    #            #self.pool.get('storage.files').grant_access(cr, uid, ids, grant_access_users)
    #        #grant_access_users = list(set(values.get('users_group')[0][2]) - set(data[0]['users_group']))
    #        #if grant_access_users:
    #        #    self.pool.get('storage.files').grant_access(cr, uid, doc_gr, grant_access_users, comment=False)
    #    return superstorage_groups, self).write(cr, uid, ids, values, context=None)

    _columns = {
        'name': fields.char('Название группы', select=True, size=256),
        'users_group': fields.many2many('res.users', 'res_user_storage_groups_rel', 'gro_id', 'usr_id', string='Список пользователей', select=True),
        'comment': fields.text('Коментарии'),
        'is_all': fields.boolean('Добавить всех'),
        'user_id': fields.many2one('res.users', 'Автор группы', select=True),
        'create_date': fields.datetime('Дата', readonly=True, select=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

storage_groups()
