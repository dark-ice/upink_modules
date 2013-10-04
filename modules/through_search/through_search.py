# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Karbanovich Andrey. Copyright UpSale
##############################################################################

import re
from osv import fields, osv


class crm_lead(osv.osv):
    _name = "crm.lead"
    _inherit = "crm.lead"

    def _get_phones(self, cr, uid, ids, field_name, arg, context=None):
        tel_obj = self.pool.get('tel.reference')
        return dict([
            (id,
             ', '.join(
                 [p.phone for p in tel_obj.browse(cr, uid, tel_obj.search(cr, uid, [('crm_lead_id', '=', id)])) if p.phone]
             )) for id in ids])

    _columns = {
        'all_phones': fields.function(
            _get_phones,
            type="char",
            obj="res.partner.address",
            method=True,
            string=u"Телефоны"
        ),
    }

crm_lead()


class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    def _get_phones(self, cr, uid, ids, field_name, arg, context=None):

        tel_obj = self.pool.get('tel.reference')

        return dict([
            (id,
             ', '.join(
                 [p.phone for p in tel_obj.browse(cr, uid, tel_obj.search(cr, uid, [('crm_lead_id', '=', id)]))]
             )) for id in ids])

    _columns = {
        'all_phones': fields.function(
            _get_phones,
            type="char",
            obj="res.partner.address",
            method=True,
            string=u"Телефоны"
        ),
    }

res_partner_address()


class through_search(osv.osv_memory):
    _name = "through.search"

    def convert(self, input, type):
        pattern = '^-?[0-9]+.?[0-9]+$'
        output = input
        #int_field = ['integer', 'datetime', 'date', 'time']
        chr_field = ['text', 'char']
        if re.match(pattern, input):
            if type == 'integer':
                try:
                    output = int(input)
                except ValueError:
                    output = ''

            if type == 'float':
                try:
                    output = float(input)
                except ValueError:
                    output = ''
        else:
            if type not in chr_field:
                output = ''

        return output

    def _get_leads(self, cr, uid, ids, field_name, field_value, arg, context=None):
        record = self.browse(cr, uid, ids, context=context)[0]
        search_str = re.sub("\s*\n\s*", ' ', record.name.strip())
        result = {}
        lead_obj = self.pool.get('crm.lead')

        args = [('company_type', "in", ("upsale", None)), ('name', 'ilike', search_str), '|', ('email_from', 'ilike', search_str), '|', ('email_2', 'ilike', search_str), '|', ('site_url_1', 'ilike', search_str), '|', ('site_url_2', 'ilike', search_str), '|', ('phone_ids.phone', 'ilike', search_str)]

        leads = lead_obj.search(cr, uid, args)
        result[record.id] = leads
        return result

    def _get_briefs(self, cr, uid, ids, field_name, field_value, arg, context=None):
        record = self.browse(cr, uid, ids, context=context)[0]
        search_str = re.sub("\s*\n\s*", ' ', record.name.strip())
        result = {}
        brief_obj = self.pool.get('brief.main')

        fields = brief_obj.fields_get(cr, uid, [])
        states = []

        for s in fields.get('state')['selection']:
            if search_str.lower() in s[1].lower():
                states.append(s[0])

        args = ['|', '|', '|', ('state', 'in', states), ('notes', 'ilike', search_str), ('comment_mp', 'ilike', search_str), ('web_sites', 'ilike', search_str)]

        briefs = brief_obj.search(cr, uid, args)
        result[record.id] = briefs
        return result

    def _get_partners(self, cr, uid, ids, field_name, field_value, arg, context=None):
        record = self.browse(cr, uid, ids, context=context)[0]
        search_str = re.sub("\s*\n\s*", ' ', record.name.strip())
        result = {}
        partner_obj = self.pool.get('res.partner')

        args = [('name', 'ilike', search_str), ('partner_type', 'in', ('upsale', None))]

        objs = partner_obj.search(cr, uid, args)
        result[record.id] = objs
        return result

    def _get_partner_address(self, cr, uid, ids, field_name, field_value, arg, context=None):
        record = self.browse(cr, uid, ids, context=context)[0]
        search_str = re.sub("\s*\n\s*", ' ', record.name.strip())
        result = {}
        address_obj = self.pool.get('res.partner.address')

        args = ['|', '|', '|', '|', '|', ('name', 'ilike', search_str), ('email', 'ilike', search_str), ('email_two', 'ilike', search_str), ('partner_site', 'ilike', search_str), ('partner_site_two', 'ilike', search_str), ('phone_ids.phone', 'ilike', search_str), ('company_id', 'in', [1, 4])]
        address = address_obj.search(cr, uid, args)
        result[record.id] = address
        return result

    _columns = {
        'name': fields.char(u'Строка поиска', size=250),
        'lead_ids': fields.function(_get_leads, type='one2many', obj='crm.lead', method=True, string='Кандидаты', select=True),
        'brief_ids': fields.function(_get_briefs, type='one2many', obj='brief.main', method=True, string='Бриф'),
        'partner_ids': fields.function(_get_partners, type='one2many', obj='res.partner', method=True, string='Партнеры'),
        'partner_address_ids': fields.function(_get_partner_address, type='one2many', obj='res.partner.address', method=True, string='Контакты'),
    }

    def do_search(self, cr, uid, ids, context=None):
        details = self.browse(cr, uid, ids)[0]
        return details.id

through_search()
