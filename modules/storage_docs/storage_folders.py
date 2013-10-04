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

class storage_folders(osv.osv):

    _name = "storage.folders"
    _rec_name = 'path'

    def _get_path(self, cr, uid, ids, field_name, arg, context):
        result = {}

        for obj in self.browse(cr, uid, ids, context=context):
            if obj.parent_id:
                path = '/'.join((obj.parent_id.path, obj.name or ''))
            else:
                path = obj.name
            result[obj.id] = path
        return result

    _columns = {
        'name': fields.char('Имя папки', select=True, size=64),
        'parent_id': fields.many2one('storage.folders', string='Категория', select=True),
        'path': fields.function(_get_path,
                                type='char', method=True,
                                store=True, size=512,
                                string='Полный путь'),
        'comment': fields.text('Коментарии'),
        'user_id': fields.many2one('res.users', 'Автор папки', select=True),
    }
    _defaults = {
        'user_id':  lambda self, cr, uid, context: uid,
        'parent_id': 1,
    }
storage_folders()
