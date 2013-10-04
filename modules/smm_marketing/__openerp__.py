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
    'name': 'SMM - Marketing',
    'version': '1.0',
    'category': 'SMM tools',
    'description': """
Accounts SMM
    """,
    'author': 'Upsale dep IS',
    'website': 'http://www.upsale.ru',
    'depends': ['hr',],
    'update_xml': [
        'security/smm_marketing_security.xml',
        'smm_socialnet_view.xml',
        'smm_fotohost_view.xml',
        'smm_videohost_view.xml',
        'smm_email_view.xml',
        'smm_blogs_view.xml',
        'smm_stpres_view.xml',
        'smm_forum_view.xml',
        'smm_mobphone_view.xml',
     ],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: