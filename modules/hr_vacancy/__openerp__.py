# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
    'name': 'HR - Vacancy',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
    Manages vacancy.
    """,
    'author': 'Upsale dep IS',
    'website': 'http://www.upsale.ru',
    'depends': ['hr','survey','crm','decimal_precision','hr_recruitment'],
    'update_xml': [
        'security/hr_vacancy_security.xml',
        'security/ir.model.access.csv',
        'hr_vacancy_workflow.xml',
        'hr_vacancy_view.xml',
        'hr_vacancy_data.xml',
     ],
    'installable': True,
    'active': False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
