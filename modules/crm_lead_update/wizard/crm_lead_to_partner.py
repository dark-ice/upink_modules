# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


from tools.translate import _
import re
from openerp.osv import osv, fields


class crm_lead2partner_upsale(osv.osv_memory):
    """
        Перевод кандидата в партнеры
    """
    def close_popup(fn):
        def wrapped(*args, **kw):
            return {'type': 'ir.actions.act_window_close'}
            fn(*args, **kw)
        return wrapped

    _name = 'crm.lead2partner.upsale'
    _columns = {
        'action': fields.selection([  # ('exist', 'Link to an existing partner'), \
                                    ('create', 'Create a new partner')],
                                    'Action', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'msg': fields.text('Message', readonly=True)
    }
    _defaults = {
        'action': 'create',
    }

    def view_init(self, cr, uid, fields, context=None):
        """
        This function checks for precondition before wizard executes
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values

        """
        print "Lead2partner Upsale"
        lead_obj = self.pool.get('crm.lead')
        rec_ids = context and context.get('active_ids', [])
        for lead in lead_obj.browse(cr, uid, rec_ids, context=context):
            if lead.partner_id:
                    raise osv.except_osv('Warning !', 'Партнер уже создан для этого кандидата.')
        if not context.get('type_lead'):
            raise osv.except_osv('Warning !', 'Этот действие пока не доступно, обратитесь к администратору.')

    def _create_partner(self, cr, uid, ids, context=None):
        """
            Метод создает партнера, в несколько этапов:
                !! Если партнер UpSale создание происходит с доп. параметрами (см. ТЗ)
                1. Создание объекта res.partner
                2. Создание объекта res.partner.address
                3. Во все объекты кандидата, где необходима связь с партнером
                    записывается res.partner id в соответствующие поля.
                    На данный момент: crm.phonecall
                                      tel.reference
                                      crm.services.rel.stage
                                      brief.main
            RETURNS список всех партнеров с новым
        """
        if context is None:
            context = {}
        #print 'context: ', context

        lead_obj = self.pool.get('crm.lead')
        partner_obj = self.pool.get('res.partner')
        contact_obj = self.pool.get('res.partner.address')
        #message_obj = self.pool.get('mail.message')
        call_obj = self.pool.get('crm.phonecall')
        tel_obj = self.pool.get('tel.reference')
        crm_part_prod_obj = self.pool.get('crm.patner.product')
        service_obj = self.pool.get('crm.services.rel.stage')
        brief_obj = self.pool.get('brief.main')
        communication_obj = self.pool.get('crm.communication.history')
        partner_ids = []
        partner_id = False
        contact_id = False
        section_id = False
        admin = 1
        rec_ids = context and context.get('active_ids', [])

        for data in self.browse(cr, uid, ids, context=context):
            for lead in lead_obj.browse(cr, uid, rec_ids, context=context):
                if data.action == 'create':
                    if context.get('type_lead', '') == 'upsale':
                        groups = self.pool.get('res.groups')
                        users = self.pool.get('res.users')
                        group_id = [77]
                        cr.execute("select id from res_partner where partner_type = 'upsale' order by create_date desc limit 1")
                        partner_ids = list(cr.fetchone())
                        managers = users.search(cr, uid, [('groups_id', 'in', group_id[0])], order='id')

                        if partner_ids:
                            partner_data = partner_obj.browse(cr, admin, partner_ids[0])
                            if partner_data.user_id.id in managers:
                                manager_position = managers.index(partner_data.user_id.id)
                                if managers[-1] == partner_data.user_id.id:
                                    user = managers[0]
                                    section_id = users.browse(cr, admin, managers[0]).context_section_id.id
                                else:
                                    user = managers[manager_position + 1]
                                    section_id = users.browse(cr, admin, managers[manager_position + 1]).context_section_id.id
                            else:
                                user = managers[0]
                                section_id = users.browse(cr, admin, managers[0]).context_section_id.id
                        else:
                            user = managers[0]
                            section_id = users.browse(cr, admin, managers[0]).context_section_id.id
                    else:
                        user = lead.user_id.id
                        section_id = users.browse(cr, admin, lead.user_id.id).context_section_id.id

                    # Добавим тематику и вложим в карточку партнера менеджера по продаже
                    partner_id = partner_obj.create(
                        cr,
                        admin,
                        {
                            'name': lead.partner_name or lead.contact_name or lead.name,
                            'user_id': user,
                            'company_id': lead.company_id.id,
                            'comment': lead.description,
                            'partner_type': context.get('type_lead', ''),
                            'activity': lead.activity,
                            'cand_type': lead.cand_type,
                            'sale_type': lead.sale_type,
                            'source': lead.source.id,
                            'author_id': uid,
                        })
                if lead.product_id:
                    prod_ids = [v.name.id for v in lead.product_id]
                    crm_part_prod_obj.write(cr, admin, prod_ids, {'res_partner': partner_id})

                contact_id = contact_obj.create(
                    cr,
                    admin,
                    {
                        'partner_id': partner_id,
                        'section_id': section_id,
                        'company_id': lead.company_id.id,
                        'name': lead.partner_name,
                        'fax': lead.fax,
                        'title': lead.title and lead.title.id or False,
                        'function': lead.function,
                        'street': lead.street,
                        'street2': lead.street2,
                        'zip': lead.zip,
                        'city': lead.city,
                        'country_id': lead.country_id and lead.country_id.id or False,
                        'state_id': lead.state_id and lead.state_id.id or False,
                        'state_ec': lead.state_ec,
                        'country_ec': lead.country_ec,
                        'msn': lead.msn,
                        'yahoo': lead.yahoo,
                        'gg': lead.gg,
                    })
                if lead.site_url_1:
                    s_id = self.pool.get('res.partner.address.site').create(cr, admin, {
                        'address_id': contact_id,
                        'name': lead.site_url_1
                    })
                    print "Site 1: %s" % s_id
                if lead.site_url_2:
                    s_id = self.pool.get('res.partner.address.site').create(cr, admin, {
                        'address_id': contact_id,
                        'name': lead.site_url_2
                    })
                    print "Site 2: %s" % s_id
                if lead.skype:
                    s_id = self.pool.get('res.partner.address.skype').create(cr, admin, {
                        'address_id': contact_id,
                        'name': lead.skype
                    })
                    print "Skype: %s" % s_id
                if lead.icq:
                    s_id = self.pool.get('res.partner.address.icq').create(cr, admin, {
                        'address_id': contact_id,
                        'name': lead.icq
                    })
                    print "Icq: %s" % s_id
                if lead.email_from:
                    s_id = self.pool.get('res.partner.address.email').create(cr, admin, {
                        'address_id': contact_id,
                        'name': lead.email_from
                    })
                    print "Email 1: %s" % s_id
                if lead.email_2:
                    s_id = self.pool.get('res.partner.address.email').create(cr, admin, {
                        'address_id': contact_id,
                        'name': lead.email_2
                    })
                    print "Email 2: %s" % s_id
                for call in lead.calles:
                    call_obj.write(cr, admin, [call.id], {'partner_id': partner_id})
                for tel in lead.phone_ids:
                    tel_obj.write(cr, admin, [tel.id], {'partner_address_id': contact_id})
                for service in lead.services_ids:
                    service_obj.write(cr, admin, [service.id], {'partner_id': partner_id})
                for comm in lead.comm_ids:
                    communication_obj.write(cr, admin, [comm.id], {'partner_id': partner_id})
                brief_ids = brief_obj.search(cr, admin, [('cand_id', '=', lead.id)])
                if brief_ids:
                    brief_obj.write(cr, admin, brief_ids, {'partner_id': partner_id})
                lead_obj.write(cr, admin, [lead.id], {})  # 'state': 'done'
            else:
                if data.partner_id:
                    partner_id = data.partner_id.id
                    contact_id = partner_obj.address_get(cr, admin, [partner_id])['default']

            partner_ids.append(partner_id)
            if data.action != 'no':
                vals = {}
                if partner_id:
                    vals.update({'partner_id': partner_id})
                if contact_id:
                    vals.update({'partner_address_id': contact_id})
                lead_obj.write(cr, admin, [lead.id], vals)
        return partner_id

    def make_partner(self, cr, uid, ids, context=None):
        """
            Метод вызывает создание партнера.
            @view_name - название view (своё для каждого партнера)
            @domain - фильтр записей конкретного партнера
            @res_id - список ids отсортиванный так, что бы первым был вновь созданный

            RETURN ir.actions.act_window

        """

        if context is None:
            context = {}

        value = {}
        partner_ids = self._create_partner(cr, uid, ids, context=context)
        if partner_ids:
            return {'type': 'ir.actions.act_window_close'}
        else:
            raise osv.except_osv('Warning !',
                        'Партнер не создан, обратитесь к администратору!')

crm_lead2partner_upsale()
