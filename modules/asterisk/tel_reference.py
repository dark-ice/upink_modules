# -*- coding: utf-8 -*-

##############################################################################
#
#    Authors: Tverdochleb Sergey
#    Copyright (C) 2011 - 2012 by UpSale co
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
import re
import netsvc
import logging
from osv import fields, osv

LOGGER = logging.getLogger(__name__)


class tel_reference(osv.osv):
    _name = 'tel.reference'
    _description = 'Tel references for crm_lead, res_partner and res_partner_address'
    _rec_name = 'phone'
    _columns = {
        'crm_lead_id': fields.many2one('crm.lead', u'Кандидат'),
        'res_partner_id': fields.many2one('res.partner', u'Партнер'),
        'partner_address_id': fields.many2one('res.partner.address', u'Адрес партнера'),
        'phone_type': fields.selection([('mob','Мобильный'),('stat','Стационарный'),], u'Тип телефона'),
        'phone': fields.char(u'Номер телефона', size=56, select=True),
        'phone_for_search': fields.char("Integer number phone", size=56),
    }
    _defaults = {
        'phone_type': lambda *a: 'stat',
    }

    def create(self, cr, uid, values, context=None):
        if context is None:
            context = {}
        if values.get('partner_address_id'):
            ival = self.pool.get('res.partner.address').browse(cr, uid, values['partner_address_id'], context)
            values['res_partner_id'] = ival.partner_id.id

        if values.get('phone_for_search') == None and values.get('phone') != False:
            pe = re.compile('\d+', re.UNICODE)
            try:
               t_val = "".join(pe.findall(values.get('phone')))
               values.setdefault('phone_for_search',t_val[-10:])
            except Exception, e:
                    LOGGER.notifyChannel(
                                         ("Asterisk module"),
                                         netsvc.LOG_ERROR,
                                         ("Error number create: %s") % str(e))
        elif values.get('phone') == False:
                 raise osv.except_osv(
                                     ("Error create phone"),
                                     ("Введите номер!")
                                     )
                 return False
        if not values.get('phone_for_search'):
            raise osv.except_osv(
                                 ("Error create phone"),
                                 ("В номере нет цифр. Введите номер!")
                                 )
            return False
        if len(values.get('phone_for_search')) < 10:
            raise osv.except_osv(
                                 ("Error create phone"),
                                 ("В номере тел. не может быть меньше 10 цифр!")
                                 )
            return False
        return super(tel_reference, self).create(cr, uid, values, context)

    def write(self, cr, uid, ids, values, context=None):
        if values.get('phone_for_search') == None and values.get('phone', False):
            pe = re.compile('\d+', re.UNICODE)
           # print values.get('phone')
            try:
                t_val = "".join(pe.findall(values.get('phone')))
                values.setdefault('phone_for_search',t_val[-10:])
            except Exception, e:
                    LOGGER.notifyChannel(
                                         ("Asterisk module"),
                                         netsvc.LOG_ERROR,
                                         ("Error number write: %s") % str(e))
        #~ if values.get('phone',False) == False:
                 #~ raise osv.except_osv(
                                     #~ ("Error create phone"),
                                     #~ ("Введите номер!")
                                     #~ )
                 #~ return False
        if not values.get('phone_for_search') and values.get('phone', False):
            raise osv.except_osv(
                                 ("Error write phone"),
                                 ("В номере нет цифр. Введите номер!")
                                 )
            return False
        if values.get('phone', False) and len(values.get('phone_for_search')) < 10:
            raise osv.except_osv(
                                 ("Error create phone"),
                                 ("В номере тел. не может быть меньше 10 цифр!")
                                 )
            return False
        return super(tel_reference, self).write(cr, uid, ids, values, context)

tel_reference()


class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    _columns = {
        'phone_ids': fields.one2many('tel.reference', 'partner_address_id', u'Номера телефонов', select=True)
    }

res_partner_address()


class crm_lead(osv.osv):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    _columns = {
        'phone_ids': fields.one2many('tel.reference', 'crm_lead_id', u'Номера телефонов', select=True)
    }

crm_lead()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

