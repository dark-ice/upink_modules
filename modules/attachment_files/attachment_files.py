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
from datetime import datetime, timedelta


class attach_files(osv.osv):
    _name = "attach.files"
    _description = u"Вложенния (файлы)"

    def onchange_path(self, cr, uid, ids, name, context=None):
        if name:
            name = name.replace('\\', '/').split('/')[-1]
            name = name.replace(' ', '_')
            return {'value': {'name': name}}
        return {'value': {}}

    _columns = {
        'name': fields.char(u'Имя файла', size=250, select=True),
        'file': fields.binary('Файл'),
        'object': fields.char(u'Объект', size=250),
        'obj_id': fields.integer(u'ID object'),
        'create_date': fields.datetime(u'Дата создания', readonly=True),
        'user_id': fields.many2one('res.users', u'Автор'),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'object': lambda self, cr, uid, context: context.get('object', ''),
    }


attach_files()
