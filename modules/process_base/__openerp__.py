# -*- encoding: utf-8 -*-
##############################################################################
#
#    Authors: Tverdochleb Sergey
#    Copyright (C) 2011 - 2012 by UpSale co. All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Процессы UpSale/Inksystem',
    'version': '1.0',
    'category': 'Process',
    'description': """
    """,
    'author': 'Upsale dep IS',
    'website': 'http://www.upsale.ru',
    'depends': ['base',],
    'update_xml': [
        'process_menu_view.xml',
        'sla_view.xml',
     ],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
