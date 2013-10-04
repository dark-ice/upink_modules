# -*- coding: utf-8 -*-
###############################################################################
#
#    Authors: Tverdochleb Sergey
#    Copyright (C) 2011 - 2012 by UpSale co
#
#  The OpenERP web client is distributed under the "OpenERP Public License".
#  It's based on Mozilla Public License Version (MPL) 1.1 with following
#  restrictions:
#
#  -   All names, links and logos of OpenERP must be kept as in original
#      distribution without any changes in all software screens, especially
#      in start-up page and the software header, even if the application
#      source code has been changed or updated or code has been added.
#
#  You can see the MPL licence at: http://www.mozilla.org/MPL/MPL-1.1.html
#
###############################################################################
import cherrypy
from openerp.controllers import SecuredController, actions
import openobject.errors
from openerp.utils import rpc

from openobject.tools import expose


class Asterisk_incom_calls(SecuredController):

    _cp_path = "/openerp/asterisk"

    @expose()
    def default(self):
        if not rpc.session.is_logged():
            return ''
        activ_form = rpc.RPCProxy('activ.asterisk.calls').get_lead_partner_by_phone()
        if activ_form:
            val = rpc.RPCProxy('asterisk.calls.config').check_user()
            if activ_form['type'] == 'partner':
                return actions.execute_by_id(val['act_part'],
                                             type='ir.actions.act_window',
                                             model='crm.lead',
                                             res_id=activ_form['id'],
                                             id=activ_form['id'],
                                             ids=[activ_form['id']],
                                             domain=('id', '=', activ_form['id']))
            elif activ_form['type'] == 'lead':
                return actions.execute_by_id(val['act_lead'],
                                             type='ir.actions.act_window',
                                             model='res.partner',
                                             res_id=activ_form['id'],
                                             id=activ_form['id'],
                                             ids=[activ_form['id']],
                                             domain=('id', '=', activ_form['id']))

        #raise openerp.common.warning("No active colls")

        #return actions.execute_window([], '')
        raise openobject.errors.TinyMessage(u'Нет активных звонков', u'Звонки')

        #values = rpc.RPCProxy('ir.actions.act_window').for_xml_id('crm_lead_update', 'crm_case_category_act_leads_contact_calls')
        #return values
        #return actions.execute(values, domain = ('id','=',61))
        #return actions.execute(values, model='crm.lead', id=175, ids=[175], res_id=175, domain = ('id','=',175), )
        #return actions.execute_window( [920], 'crm.lead', res_id=61, domain=[('id','=',61)], view_type='form', mode='form')
