# -*- encoding: utf-8 -*-
##############################################################################
#
#    UpSale, by Tverdokhleb Sergey
#    Copyright (C) 2004-2009 UpSale (<http://www.upsale.ru>). All Rights Reserved
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
    'name': 'HR - Recruitement Update',
    'version': '1.1',
    'category': 'Generic Modules/Human Resources',
    'description': """
Update: add field <title_action> to tree view.
    """,
    'author': 'UpSale',
    'website': 'http://www.upsale.ru',
    'depends': ['hr', 'survey', 'crm', 'decimal_precision', 'hr_recruitment'],
    'update_xml': [
        'hr_recruitment_view.xml',
    ],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
