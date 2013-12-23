# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
import re
import numpy
import pytz
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model


AVAILABLE_PRIORITIES = [
    ('1', 'Наивысший'),
    ('2', 'Высокий'),
    ('3', 'Нормальный'),
    ('4', 'Низкий'),
    ('5', 'Самый низкий'),
]

PARTNER_STATUS = (
    ('new', 'Новая'),
    ('exist', 'Существующая'),
    ('paused', 'В зоне риска'),
    ('cancel', 'Отказ'),
    ('returned', 'Возврат'),
    ('closed', 'Закрыт'),
)


CRITERIAS = (
    ('terms_of_service', 'Сроки предоставления услуги'),
    ('conformity', 'Соответствие услуги всем входным требованиям, указанным в ТЗ'),
    ('quality_feedback', 'Качество обратной связи с представителем Компании , скорость и полнота ответов менеджера'),
    ('completeness_of_reporting', 'Полнота отчетов о результатах рекламной кампании и соблюдение сроков их предоставления'),
)


SERVISE_TYPE = (
    ('project', 'Проектная'),
    ('process', 'Процессная'),
)


def get_state(states, state):
    return [item for item in states if item[0] == state][0]


class res_partner_address(Model):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    def email_to_partner(self, cr, uid, ids, context=None):
        """
            Отправляет письмо по адресу партнера
        """
        action_id = self.pool.get('ir.actions.act_window').search(cr, uid, [('name', '=', 'Письмо кандидату')],
                                                                  context=context)
        if action_id:
            data = self.pool.get('ir.actions.act_window').read(cr, uid, action_id[0], context=context)
            accounts = self.pool.get('poweremail.core_accounts').search(cr, uid, [('user', '=', uid)])
            partner_address_data = self.browse(cr, uid, ids[0])
            if len(accounts) == 1:
                user_account = accounts[0]
            else:
                user_account = False
            data.update({
                'nodestroy': True,
                'context': {
                    'partner': ids[0],
                    'pem_to': partner_address_data.email,
                    'pem_account_id': user_account,
                    'state': 'na',
                    'folder': 'outbox',
                }
            })
            return data
        return False

    def _get_phones(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids)

        for address in data:
            res[address.id] = ",\n".join([a.phone for a in address.phone_ids if a.phone])
        return res

    def _get_skype(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids)

        for address in data:
            res[address.id] = ",\n".join([a.name for a in address.skype_ids if a.name])
        return res

    def _get_site(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids)

        for address in data:
            res[address.id] = ",\n".join([a.name for a in address.site_ids if a.name])
        return res

    def _get_email(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids)

        for address in data:
            res[address.id] = ",\n".join([a.name for a in address.email_ids if a.name])
        return res

    def _get_icq(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids)

        for address in data:
            res[address.id] = ",\n".join([a.name for a in address.icq_ids if a.name])
        return res

    def _search_site(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('res.partner.address.site').search(cr, uid, [('name', args[0][1], args[0][2])],
                                                                    context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('site_ids', 'in', site_ids)],
                                                                  context=context)
        if address_ids:
            return [('id', 'in', address_ids)]
        return [('id', '=', '0')]

    def _search_phone(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('tel.reference').search(
            cr,
            uid,
            [
                '|', ('phone', args[0][1], args[0][2]),
                ('phone_for_search', args[0][1], args[0][2])
            ],
            context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('phone_ids', 'in', site_ids)],
                                                                  context=context)

        if address_ids:
            return [('id', 'in', address_ids)]
        return [('id', '=', '0')]

    def _search_email(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('res.partner.address.email').search(cr, uid, [('name', args[0][1], args[0][2])],
                                                                     context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('email_ids', 'in', site_ids)],
                                                                  context=context)

        if address_ids:
            return [('id', 'in', address_ids)]
        return [('id', '=', '0')]

    def _search_skype(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('res.partner.address.skype').search(cr, uid, [('name', args[0][1], args[0][2])],
                                                                     context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('skype_ids', 'in', site_ids)],
                                                                  context=context)

        if address_ids:
            return [('id', 'in', address_ids)]
        return [('id', '=', '0')]

    def _search_icq(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('res.partner.address.icq').search(cr, uid, [('name', args[0][1], args[0][2])],
                                                                   context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('icq_ids', 'in', site_ids)],
                                                                  context=context)
        if address_ids:
            return [('id', 'in', address_ids)]
        return [('id', '=', '0')]

    def _check_site_full(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, ['site_ids', 'partner_id']):
            if not record['partner_id']:
                return True
            if not record['site_ids']:
                return False
        return True

    def _check_phone_full(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, ['phone_ids', 'partner_id']):
            if not record['partner_id']:
                return True
            if not record['phone_ids']:
                return False
        return True

    def insert_site_name(self, cr, uid, ids, context):
        if context.get('site_ids'):
            return {'value': {'site_ids': [(0, 0, {'name': context['site_ids']})], }}

    _columns = {
        'state_ec': fields.char('Область', size=250),
        'country_ec': fields.char('Страна', size=250),
        'partner_site': fields.char('Сайт партнера', size=250),
        'partner_site_two': fields.char('Сайт партнера (2)', size=250),
        'email_two': fields.char('Эл.Почта (2)', size=250),
        'skype': fields.char('Skype', size=250),
        'msn': fields.char('MSN', size=250),
        'yahoo': fields.char('Yahoo', size=250),
        'icq': fields.char('ICQ', size=250),
        'gg': fields.char('GG', size=250),
        'site_ids': fields.one2many('res.partner.address.site', 'address_id', 'Сайты', required=True),
        'skype_ids': fields.one2many('res.partner.address.skype', 'address_id', 'Skype'),
        'icq_ids': fields.one2many('res.partner.address.icq', 'address_id', 'ICQ'),
        'email_ids': fields.one2many('res.partner.address.email', 'address_id', 'Эл. почта'),

        'phones_all': fields.function(_get_phones, type="char", obj="res.partner.address", method=True,
                                      string="Телефоны", fnct_search=_search_phone),
        'phone_default': fields.related('phone_ids', 'phone', type='char', size=128, string='Телефон'),

        'skype_all': fields.function(_get_skype, type="char", obj="res.partner.address", method=True, string="Skype",
                                     fnct_search=_search_skype),
        'skype_default': fields.related('skype_ids', 'name', type='char', size=128, string='Skype'),

        'site_all': fields.function(_get_site, type="char", obj="res.partner.address", method=True, string="Сайты",
                                    fnct_search=_search_site),
        'site_default': fields.related('site_ids', 'name', type='char', size=128, string='Сайт'),
        'email_all': fields.function(_get_email, type="char", obj="res.partner.address", method=True,
                                     string="Эл. почта", fnct_search=_search_email),
        'email_default': fields.related('email_ids', 'name', type='char', size=128, string='Эл. почта'),
        'icq_all': fields.function(
            _get_icq,
            type="char",
            obj="res.partner.address",
            method=True,
            string="ICQ",
            fnct_search=_search_icq
        ),
        'icq_default': fields.related('icq_ids', 'name', type='char', size=128, string='ICQ'),
        'main_face': fields.boolean('Главное контактное лицо')
    }
    _constraints = [
        (
            _check_site_full,
            'должен быть указан!',
            [u'Сайт']
        ),
        (
            _check_phone_full,
            'должен быть указан!',
            [u'Телефон']
        ),
    ]

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = []
        for r in self.read(cr, user, ids, ['name','zip','country_id', 'city','partner_id', 'street']):
            if context.get('contact_display', 'contact')=='partner' and r['partner_id']:
                res.append((r['id'], r['partner_id'][1]))
            else:
                # make a comma-separated list with the following non-empty elements
                elems = [r['country_id'] and r['country_id'][1], r['city'], r['street']]
                addr = ', '.join(filter(bool, elems))
                if (context.get('contact_display', 'contact')=='partner_address') and r['partner_id']:
                    res.append((r['id'], "%s: %s" % (r['partner_id'][1], addr or '/')))
                else:
                    res.append((r['id'], addr or '/'))
        return res

    def check_main(self, cr, select_id, partner_id):
        main_ids = self.search(cr, 1, [('partner_id', '=', partner_id), ('main_face', '=', True), ('id', '!=', select_id)])
        if main_ids:
            self.write(cr, 1, main_ids, {'main_face': False})

    def create(self, cr, user, vals, context=None):
        new_id = super(res_partner_address, self).create(cr, user, vals)
        if vals.get('main_face'):
            self.check_main(cr, new_id, vals['partner_id'])
        return new_id

    def write(self, cr, user, ids, vals, context=None):
        flag = super(res_partner_address, self).write(cr, user, ids, vals, context)
        if flag and vals.get('main_face'):
            for record in self.read(cr, user, ids, ['partner_id']):
                self.check_main(cr, record['id'], record['partner_id'][0])
        return flag


res_partner_address()


class res_provider_category(Model):
    _description = u'Категория Поставщика'
    _name = 'res.provider.category'
    _order = 'name'
    _columns = {
        'name': fields.char('Категория поставщика', size=256, required=True),
    }
res_provider_category()


class partner_added_services(Model):
    _name = "partner.added.services"
    _rec_name = 'comment'

    def _get_service_status(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            val = 'Новая'

            if record.service_id.service_type == 'project':
                launch_ids = self.pool.get('process.launch').search(cr, 1, [('partner_id', '=', record.partner_id.id), ('service_id', '=', record.service_id.id)])
                if launch_ids:
                    launch = self.pool.get('process.launch').read(cr, 1, launch_ids[-1], ['process_model', 'process_id'])
                    if launch['process_model'] and launch['process_id']:
                        process = self.pool.get(launch['process_model']).read(cr, 1, launch['process_id'], ['state', 'create_date'])
                        if process:
                            if process['state'] == 'finish':
                                val = 'Закрыт'
                            elif datetime.strptime(process['create_date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC) + timedelta(days=15) < datetime.now(pytz.UTC):
                                val = 'Существующая'

            elif record.service_id.service_type == 'process':
                invoice_ids = self.pool.get('account.invoice').search(cr, 1, [('partner_id', '=', record.partner_id.id)])
                pay_ids = self.pool.get('account.invoice.pay.line').search(cr, 1, [('invoice_id', 'in', invoice_ids), ('service_id', '=', record.service_id.id)])
                if pay_ids:
                    first_pay = self.pool.get('account.invoice.pay.line').read(cr, 1, pay_ids[0], ['pay_date'])
                    last_pay = self.pool.get('account.invoice.pay.line').read(cr, 1, pay_ids[-1], ['pay_date'])
                    pre_last_pay = None
                    if len(pay_ids) > 1:
                        pre_last_pay = self.pool.get('account.invoice.pay.line').read(cr, 1, pay_ids[-2], ['pay_date'])

                    if pre_last_pay is not None and pre_last_pay.get('pay_date') and datetime.strptime(pre_last_pay['pay_date'], "%Y-%m-%d").replace(tzinfo=pytz.UTC) + timedelta(days=90) < datetime.strptime(last_pay['pay_date'], "%Y-%m-%d").replace(tzinfo=pytz.UTC):
                        val = 'Возврат'

                    if datetime.strptime(first_pay['pay_date'], "%Y-%m-%d").replace(tzinfo=pytz.UTC) + timedelta(days=30) < datetime.now(pytz.UTC):
                        val = 'Существующая'
                    if datetime.strptime(last_pay['pay_date'], "%Y-%m-%d").replace(tzinfo=pytz.UTC) + timedelta(days=40) < datetime.now(pytz.UTC):
                        val = 'В зоне риска'
                    if datetime.strptime(last_pay['pay_date'], "%Y-%m-%d").replace(tzinfo=pytz.UTC) + timedelta(days=90) < datetime.now(pytz.UTC):
                        val = 'Отказ'

            res[record.id] = val
        return res

    def _set_check(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['date_start', 'date_finish', 'partner_id', 'service_id']):
            if record['date_start'] and record['date_finish']:
                if record['date_start'] <= date.today().strftime('%Y-%m-%d') <= record['date_finish']:
                    res[record['id']] = True
                else:
                    res[record['id']] = False
            elif record['date_start'] and not record['date_finish']:
                if record['date_start'] <= date.today().strftime('%Y-%m-%d'):
                    res[record['id']] = True
                elif record['date_start'] > date.today().strftime('%Y-%m-%d'):
                    res[record['id']] = False
            else:
                res[record['id']] = False
        return res

    _columns = {
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'comment': fields.text('Комментарий'),
        'date_start': fields.date('Дата подключения'),
        'date_finish': fields.date('Дата окончания'),
        'partner_id': fields.many2one('res.partner', 'Партнер', inbisible=True),
        'check': fields.function(_set_check, type="boolean", method=True, string='Статус подключения'),
        'budget': fields.float('Бюджет, y.e.'),
        'partner_base': fields.related('partner_id', 'partner_base', type='char', size=50),
        'service_status': fields.function(
            _get_service_status,
            method=True,
            string='Статус',
            type='char',
            size=200,
        ),
        'history_id': fields.integer(),
        'history_ids': fields.one2many('partner.added.services.history', 'history_service_id', 'ids истории'),

    }

    _defaults = {
        'partner_base': lambda s, cr, u, cnt: cnt.get('partner_base')
    }

    def connect_service(self, cr, partner_id, service_id, date_start):
        flag = False
        as_ids = self.search(cr, 1, [('partner_id', '=', partner_id), ('service_id', '=', service_id)])
        h_ids = self.pool.get('partner.added.services.history').search(cr, 1, [('history_service_id', 'in', as_ids), ('date_finish', '=', False)])
        vals = {
            'partner_id': partner_id,
            'service_id': service_id,
            'date_start': date_start,
        }
        if date_start:
            if not h_ids:
                lines = [(0, 0, vals)]
            else:
                lines = [(1, h_ids[0], vals)]
            for service in self.read(cr, 1, as_ids, ['budget', 'comment']):
                vals.update({
                    'budget': service['budget'],
                    'comment': service['comment'],
                })
                flag = self.write(
                    cr,
                    1,
                    as_ids,
                    {
                        'date_start': date_start,
                        'date_finish': False,
                        'history_ids': lines
                    })
        return flag

    def set_all_services(self, cr, uid, ids, context=None):
        invoice_ids = self.pool.get('account.invoice').search(cr, 1, [('type', '=', 'out_invoice')], order='date_invoice')
        vals = {}
        for i in self.pool.get('account.invoice').read(cr, 1, invoice_ids, ['partner_id', 'date_invoice', 'invoice_line']):
            for j in self.pool.get('account.invoice.line').read(cr, 1, i['invoice_line'], ['service_id']):
                if i['partner_id'] and j['service_id']:
                    if not vals.get((i['partner_id'][0], j['service_id'][0])):
                        vals[(i['partner_id'][0], j['service_id'][0])] = i['date_invoice']

        process_ids = self.pool.get('process.launch').search(cr, 1, [])
        for p in self.pool.get('process.launch').read(cr, 1, process_ids, ['partner_id', 'service_id', 'create_date']):
            if p['partner_id'] and p['service_id']:
                if not vals.get((p['partner_id'][0], p['service_id'][0])):
                    vals[(p['partner_id'][0], p['service_id'][0])] = p['create_date']
        for k, v in vals.iteritems():
            self.connect_service(cr, k[0], k[1], v)

partner_added_services()


class PartnerAddedServicesHistory(Model):
    _name = "partner.added.services.history"

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['responsible_id', 'specialist_id', 'service_head_id'], context):
            access = str()

            #  Специалисты
            if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', ['49', '50', '85', '89'])]):
                access += 'r'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'history_service_id': fields.integer('Id'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'direction': fields.related(
            'service_id',
            'direction',
            string='Направление',
            type='char',
            size=10,
            store=True,
        ),
        'comment': fields.text('Комментарий'),
        'date_start': fields.date('Дата подключения'),
        'date_finish': fields.date('Дата окончания'),
        'partner_id': fields.many2one('res.partner', 'Партнер', inbisible=True),
        'budget': fields.float('Бюджет, y.e.'),
        'partner_base': fields.related('partner_id', 'partner_base', type='char', size=50),
        'history_ids': fields.one2many('partner.added.services.change.history', 'history_service_id', 'ids истории'),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Проверка',
            type='boolean',
            invisible=True
        ),

        'date_start_from': fields.date('Дата начала с'),
        'date_start_to': fields.date('Дата начала по'),
        'date_finish_from': fields.date('Дата окончания с'),
        'date_finish_to': fields.date('Дата окончания по'),
    }

    def change_history(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'partner.added.services.history.form'), ('model', '=', self._name)])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'name': 'Изменить даты в истории',
            'view_id': view_id,
            'res_id': ids[0] if ids else 0,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        }

    def save(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def write(self, cr, user, ids, vals, context=None):
        for record in self.read(cr, user, ids, ['date_start', 'date_finish', 'partner_id', 'service_id']):
            if (vals.get('date_finish') and vals['date_finish'] != record['date_finish']) or (vals.get('date_start') and vals['date_start'] != record['date_start']):
                vals.update({'history_ids': [(0, 0, {
                    'partner_id': record['partner_id'][0],
                    'service_id': record['service_id'][0],

                    'date_start': vals.get('date_start') or record['date_start'],
                    'old_date_start': record['date_start'],

                    'date_finish': vals.get('date_finish') or record['date_finish'],
                    'old_date_finish': record['date_finish'],
                })]})
        return super(PartnerAddedServicesHistory, self).write(cr, user, ids, vals, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=None):
        sql_postfix = []
        date_st_to = None
        date_fn_to = None
        date_st_from = None
        date_fn_from = None
        date_indx = []

        for indx, item in enumerate(args):
            if 'date_start_from' == item[0]:
                date_st_from = item[2]
                date_indx.append(indx)
            if 'date_start_to' == item[0]:
                date_st_to = item[2]
                date_indx.append(indx)
            if 'date_finish_to' == item[0]:
                date_fn_to = item[2]
                date_indx.append(indx)
            if 'date_finish_from' == item[0]:
                date_fn_from = item[2]
                date_indx.append(indx)

        if date_st_from is not None and date_st_to is None:
            sql_postfix.append("date_start='{0}'::date".format(date_st_from,))
        elif date_st_from is not None and date_st_to is not None:
            sql_postfix.append("date_start between '{0}'::date and '{1}'::date".format(date_st_from, date_st_to))

        if date_fn_from is not None and date_fn_to is None:
            sql_postfix.append("date_finish='{0}'::date".format(date_fn_from,))
        elif date_fn_from is not None and date_fn_to is not None:
            sql_postfix.append("date_finish between '{0}'::date and '{1}'::date".format(date_fn_from, date_fn_to))

        sql_postfix_str = ' AND '.join(sql_postfix)
        if sql_postfix_str:
            sql = 'SELECT id FROM partner_added_services_history WHERE {0}'.format(sql_postfix_str,)
            cr.execute(sql)
            res_ids = set(service_id[0] for service_id in cr.fetchall())
            args.append(['id', 'in', tuple(res_ids)])

        if date_indx:
            date_indx.sort()
            date_indx.reverse()
            for indx in date_indx:
                del args[indx]
        return super(PartnerAddedServicesHistory, self).search(cr, uid, args, offset, limit, order, context, count)

PartnerAddedServicesHistory()


class PartnerAddedServicesChangeHistory(Model):
    _name = "partner.added.services.change.history"
    _columns = {
        'history_service_id': fields.integer('ID'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'date_start':fields.date('Дата подключения'),
        'old_date_start':fields.date('Старая Дата подключения'),
        'date_finish':fields.date('Дата окончания'),
        'old_date_finish':fields.date('Старая Дата окончания'),
        'partner_id': fields.many2one('res.partner', 'Партнер', inbisible=True),
        'create_uid': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата Изменения', readonly=True),
    }


class bonus_reason(Model):
    _description = u'List of reasons for bonus'
    _name = 'partner.bonus.reason'

    _columns = {
        'name': fields.char('Причина бонуса', size=250),
    }
bonus_reason()


class refusion_reason(Model):
    _description = u'Reasons of refusion'
    _name = 'partner.refusion.reason'

    _columns = {
        'name': fields.char('Название', size=250),
    }
refusion_reason()


class operational_departments(Model):
    _description = u'Operational directions'
    _name = 'partner.operational.departments'
    _rec_name = 'department'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'department': fields.many2one('hr.department', 'Направление'),
        'specialist': fields.many2one('hr.employee', 'Специалист', domain="[('department_id','=', department)]"),
    }
operational_departments()


class partner_dealer_discount(Model):
    _description = u'Dealer discount for partners'
    _name = 'partner.dealer.discount'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнер', invisible=True),
        'amount': fields.float('Размер скидки'),
        'date': fields.datetime('Дата'),
    }
partner_dealer_discount()


class order_type(Model):
    _description = u'Types of orders for History of partners orders'
    _name = 'partner.order.type'

    _columns = {
        'name': fields.char('Название', size=250),
    }
order_type()


class shipment_type(Model):
    _description = u'Shipment types for History of partners orders'
    _name = 'partner.shipment.type'

    _columns = {
        'name': fields.char('Название', size=250),
    }
shipment_type()


class payment_state(Model):
    _description = u'Payment states for History of partners orders'
    _name = 'partner.payment.state'

    _columns = {
        'name': fields.char('Название', size=250),
    }
payment_state()


class partner_currency(Model):
    _description = u'List of currencies for History of partners orders'
    _name = 'partner.currency'

    _columns = {
        'name': fields.char('Название', size=20),
    }
partner_currency()


class partner_order_history(Model):
    """
        Объект История заказов.
        Используется в res.partner
            Связь one2many
    """

    _description = u'History of partner orders'
    _name = 'partner.order.history'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'type': fields.many2one('partner.order.type', 'Тип'),
        'create_date': fields.datetime('Дата', readonly=True),
        'number': fields.char('Номер', size=50),
        'shipment_type': fields.many2one('partner.shipment.type', 'Тип отгрузки'),
        'sum': fields.float('Сумма'),
        'currency': fields.many2one('partner.currency', 'Валюта'),
        'payment_state': fields.many2one('partner.payment.state', 'Статус оплаты'),
        'user_id': fields.many2one('res.users', 'Автор', readonly=True),
        'commentary': fields.text('Комментарий'),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
partner_order_history()


class PartnerReferencesTemplate(Model):
    _name = 'partner.template.references'
    _description = u'Template for similar references for partner'
    _auto = False

    _columns = {
        'name': fields.char('Название', size=250, select=True),
    }
PartnerReferencesTemplate()


class PayType(Model):
    _name = 'partner.pay.type'
    _inherit = 'partner.template.references'
    _auto = True
    _description = u'Способы оплаты'
PayType()


class PartnerState(Model):
    _name = 'partner.partner.state'
    _inherit = 'partner.template.references'
    _auto = True
    _description = u'Статус партнера'
PartnerState()


class DeliveryType(Model):
    _name = 'partner.delivery.type'
    _inherit = 'partner.template.references'
    _auto = True
    _description = u'Способ доставки'
DeliveryType()


class DeliveryFrom(Model):
    _name = 'partner.delivery.from'
    _inherit = 'partner.template.references'
    _auto = True
    _description = u'Откуда делается доставка'
DeliveryFrom()


class res_partner_circulation(Model):
    _name = "res.partner.circulation"
    _order = "date_id desc"

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', invisible=True),
        'date_id': fields.many2one('sla.interval.date', 'Период', select=True),
        'type': fields.selection(
            [
                ('fact', 'Факт'),
                ('plan', 'План'),
            ], 'Тип'
        ),
        'total': fields.float("Общий оборот", digits=(12, 2)),
        'printers': fields.float("Оборот по принтерам", digits=(12, 2)),
        'inksystem': fields.float("Оборот по продукции INKSYSTEM", digits=(12, 2)),
    }

    _rec_name = "inksystem"
res_partner_circulation()


class res_partner_access(Model):
    _name = 'res.partner.access'
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнер', invisible=True),
        'type': fields.selection(
            [
                ('ftp', 'ftp'),
                ('db', 'База данных'),
                ('admin', 'Система администрирования'),
                ('hosting', 'Хостинг'),
                ('upSale', 'Доступ в ЛК UpSale'),
                ('googleAnalytics', 'Доступ в GoogleAnalytics'),
                ('yandexMetrica', 'Доступ в YandexMetrica'),
                ('googleAdWords', 'Доступ в GoogleAdWords'),
                ('yandexDirect', 'Доступ в ЯндексДирект'),
            ], 'Доступы партнера', required=True),
        'link': fields.char('Ссылка', size=250),
        'login': fields.char('Логин', size=250, required=True),
        'pswd': fields.char('Пароль', size=250, required=True),
    }
res_partner_access()


class res_partner_address_site(Model):
    _name = "res.partner.address.site"
    _description = u'Сайты'
    _columns = {
        'address_id': fields.many2one('res.partner.address', 'Address', invisible=True),
        'name': fields.char('Сайт', size=250, select=True, required=True),
    }
res_partner_address_site()


class res_partner_address_skype(Model):
    _name = "res.partner.address.skype"

    _columns = {
        'address_id': fields.many2one('res.partner.address', 'Address', invisible=True),
        'name': fields.char('Skype', size=250, select=True, required=True),
    }
res_partner_address_skype()


class res_partner_address_icq(Model):
    _name = "res.partner.address.icq"

    _columns = {
        'address_id': fields.many2one('res.partner.address', 'Address', invisible=True),
        'name': fields.char('ICQ', size=250, select=True, required=True),
    }
res_partner_address_icq()


class res_partner_address_email(Model):
    _name = "res.partner.address.email"

    _columns = {
        'address_id': fields.many2one('res.partner.address', 'Address', invisible=True),
        'name': fields.char('Email', size=250, select=True, required=True),
    }
res_partner_address_email()


class res_partner_bank(Model):
    _name = "res.partner.bank"
    _inherit = "res.partner.bank"
    _description = u"Реквизиты партнера"

    def _get_bankname(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids, context)
        for field in data:
            n = ''
            if field.name:
                n = field.name
            elif field.fullname:
                n = field.fullname
            else:
                n = "Empty"
            res[field.id] = field.name or field.fullname or "Реквизиты"
        return res

    def name_get(self, cr, uid, ids, context=None):
        return [(r['id'], tools.ustr(r['fullname'])) for r in
                self.read(cr, uid, ids, ['fullname'], context, load='_classic_write')]

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if args is None:
            args = []
        if context is None:
            context = {}
        args = args[:]
        # optimize out the default criterion of ``ilike ''`` that matches everything
        #if not (name == '' and operator == 'ilike'):
        args += [('fullname', operator, name)]
        ids = self._search(cr, user, args, limit=limit, context=context, access_rights_uid=user)
        res = self.name_get(cr, user, ids, context)
        return res

    _columns = {
        'name': fields.char(u'Сокращённое наименование партнёра', size=250, required=False),
        'state': fields.char(u'State', size=1, required=False),
        'bank': fields.char(u'Банк', size=250, required=False),
        'partner_id': fields.many2one('res.partner', u'Партнер', required=False),

        'acc_number': fields.function(_get_bankname, type="text", method=True, string=u"Название счета"),

        'type': fields.selection(
            [
                ('ur', 'Юридического лицо'),
                ('ch', 'Частное лицо'),
                ('ip', 'Индивидуальный предприниматель')
            ], u'Тип'),
        'fullname': fields.char(u"Полное наименование партнёра", size=250),
        'address_ids': fields.one2many('res.partner.bank.address', 'bank_id', u'Адресс'),
        'email': fields.char(u'Электронная почта', size=250),
        'phone': fields.char(u'Телефон (при наличии)', size=64),
        'fax': fields.char(u'Факс (при наличии)', size=64),
        'site': fields.char(u'Сайт (при наличии)', size=250),
        'ogrn': fields.char(u"ОГРН", size=13),
        'inn': fields.char(u"ИНН", size=10),
        'kpp': fields.char(u"КПП", size=9),
        'okpo': fields.char(u"ЭДРПОУ (ОКПО)", size=8),
        'mfo': fields.char(u"МФО", size=6),
        'current_account': fields.char(u"Расчетный счет", size=20),
        'correspondent_account': fields.char(u"Корреспондентский счёт", size=20),
        'bik': fields.char(u"БИК (Банковский идентификационный код)", size=9),
        'ogrnip': fields.char(u"ОГРНИП", size=15),

        'passport': fields.text(u"Паспорт", help=u"Серия, номер паспорта, кем и когда выдан"),
        'address_registration': fields.text(u"Адрес регистрации"),

    }

    _defaults = {
        'state': lambda *a: '1',
        'partner_id': lambda self, cr, uid, context: context.get('partner_id', False)
    }
res_partner_bank()


class ResPartnerBankAddress(Model):
    _name = "res.partner.bank.address"
    _description = u"Реквизиты партнера - Адрес"
    _columns = {
        'name': fields.selection(
            [
                ('ua', 'Юридический адрес'),
                ('fa', 'Фактический адрес'),
                ('mk', 'Адрес для почтовой корреспонденции')
            ], 'Тип'),
        'index': fields.char("Почтовый индекс", size=6),
        'city': fields.char("Город", size=250),
        'st_type': fields.selection(
            [
                ('alleya', 'Аллея'),
                ('ylitsa', 'Улица'),
                ('bulvar', 'Бульвар'),
                ('naberegnaya', 'Набережная'),
                ('pereyloc', 'Переулок'),
                ('proezd', 'Проезд'),
                ('prospect', 'Проспект'),
                ('ploshad', 'Площадь'),
            ], 'Тип улицы'),
        'street': fields.char("Улица", size=250),
        'house': fields.char("№ дома", size=50),
        'housing': fields.char("№ корпуса", size=50),
        'building': fields.char("№ строения", size=50),
        'flat_type': fields.selection(
            [
                ('flat', 'Квартира'),
                ('room', 'Комната'),
                ('cabinet', 'Кабинет'),
                ('office', 'Офис'),
                ('aya', 'а/я'),
                ('sota', 'Ячейка'),
                ('etc', 'Иное')
            ], 'Тип помещения'),
        'flat': fields.char("№ помещения", size=50),
        'bank_id': fields.many2one('res.partner.bank', 'Bank', invisible=True),
    }

    _defaults = {
        'name': 'ua',
        'flat_type': 'flat',
        'st_type': 'ylitsa'
    }

    def get_address(self, cr, bank_id, address_type='ua'):
        address_ids = self.search(cr, 1, [('bank_id', '=', bank_id), ('name', '=', address_type)])
        address_list = []
        if address_ids:
            address = self.read(cr, 1, address_ids[0], [])
            if address['index']:
                address_list.append(address['index'])
            if address['city']:
                address_list.append(address['city'])
            if address['street']:
                st = u'ул.'
                if address['st_type'] == 'alleya':
                    st = u'ал.'
                if address['st_type'] == 'bulvar':
                    st = u'бул.'
                if address['st_type'] == 'naberegnaya':
                    st = u'наб.'
                if address['st_type'] == 'pereyloc':
                    st = u'пр.'
                if address['st_type'] == 'proezd':
                    st = u'проезд'
                if address['st_type'] == 'prospect':
                    st = u'просп.'
                if address['st_type'] == 'ploshad':
                    st = u'пл.'
                address_list.append(u"{st_type} {street}".format(street=address['street'], st_type=st))
            if address['house']:
                address_list.append(u"д. {house}".format(house=address['house']))
        return ','.join(address_list) or u'-'
ResPartnerBankAddress()


class SkkNotes(Model):
    _name = 'skk.notes'
    _inherit = 'crm.lead.notes'
    _description = u"Заметки кандидатов"
SkkNotes()


class ResPartner(Model):
    _inherit = "res.partner"
    _description = u'Partner'
    _order = "priority, create_date desc"

    def change_name(self, cr, uid, ids, ur_name='', site='', context=None):
        return {'value': {'name': self._get_name(ur_name, site)}}

    @staticmethod
    def _get_name(ur_name='', site=''):
        if ur_name:
            name = ur_name.encode('utf-8')
        else:
            name = ''
        if site and ur_name:
            name += ' ({0})'.format(site.encode('utf-8'))
        elif site and not ur_name:
            name += '{0}'.format(site.encode('utf-8'))
        return name

    def _last_circulation(self, cr, uid, ids, field, arg, context):
        res = {}
        for record in self.browse(cr, uid, ids):
            if len(record.circulation):
                circulation = record.circulation[0].inksystem or 0.0
            else:
                circulation = 0.0
            res[record.id] = circulation
        return res

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        flag = False
        if uid in (1, 14):
            flag = True
        return dict([(record_id, flag) for record_id in ids])

    def _get_service(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids):
            if record.brief_ids:
                res[record.id] = record.brief_ids[0].services_ids.id
            else:
                res[record.id] = False
        return res

    def _get_report_payment(self, cr, uid, ids, name, arg, context=None):
        res = {}
        sum_list = {}
        pay_pool = self.pool.get('account.invoice.pay')
        for record in self.read(cr, uid, ids, ['invoice_ids']):
            pay_ids = pay_pool.search(cr, 1, [('invoice_id', 'in', record['invoice_ids'])], order='date_pay')
            for pay in pay_pool.read(cr, 1, pay_ids, ['total', 'date_pay', 'invoice_id']):
                invoice = self.pool.get('account.invoice').read(cr, 1, pay['invoice_id'][0], ['rate'])
                date_pay = datetime.strptime(pay['date_pay'], "%Y-%m-%d")
                period = self.pool.get('kpi.period').get_by_date(cr, date_pay, calendar='rus')
                try:
                    sum_list[period.id] += pay['total'] / invoice['rate']
                except KeyError:
                    sum_list[period.id] = pay['total'] / invoice['rate']
            res[record['id']] = [(0, 0, {'period_id': k, 'payment_sum': v}) for k, v in sum_list.iteritems()]

        return res

    def _get_rate(self, cr, uid, ids, name, arg, context=None):
        res = {}
        fields = [
            'description',
            'key_person',
            'key_moment',
            'zone',
            'another',
            'terms_of_service',
            'conformity',
            'quality_feedback',
            'completeness_of_reporting',
        ]
        for record in self.read(cr, 1, ids, fields):
            rate = 0.0

            if self.pool.get('partner.operational.departments').search(cr, 1, [('partner_id', '=', record['id'])], count=True):
                rate += 5.0

            if self.pool.get('ir.attachment').search(cr, 1, [('res_id', '=', record['id']), ('res_model', '=', 'res.partner')], count=True) >= 2:
                rate += 10.0

            if self.pool.get('res.partner.access').search(cr, 1, [('partner_id', '=', record['id'])], count=True):
                rate += 10.0

            services_ids = self.pool.get('partner.added.services').search(cr, 1, [('partner_id', '=', record['id'])])
            if services_ids:

                flag = True
                for service in self.pool.get('partner.added.services').read(cr, 1, services_ids, ['service_id', 'comment', 'budget']):
                    if not service['service_id'] or not (service['comment'] and service['comment'].split()) or not service['budget']:
                        flag = False
                        break
                if flag:
                    rate += 10.0

            if record['terms_of_service'] and record['terms_of_service'].split() and record['conformity'] and record['conformity'].split() and record['quality_feedback'] and record['quality_feedback'].split() and record['completeness_of_reporting'] and record['completeness_of_reporting'].split():
                rate += 5.0

            if record['description'] and len(record['description'].strip()) > 15:
                rate += 5.0

            if record['key_person'] and len(record['key_person'].strip()) > 15:
                rate += 10.0

            if record['key_moment'] and len(record['key_moment'].strip()) > 15:
                rate += 10.0

            if record['zone'] and len(record['zone'].strip()) > 15:
                rate += 5.0

            if record['another'] and len(record['another'].strip()) > 15:
                rate += 5.0

            note_ids = self.pool.get('crm.lead.notes').search(cr, 1, [('partner_id', '=', record['id']), ('type', '!=', 'skk')])
            if note_ids:
                note_last = self.pool.get('crm.lead.notes').read(cr, 1, note_ids[0], ['create_date'])
                week_day = date.today().weekday()
                td = 3
                if week_day in (5, 6):
                    td = week_day - 4
                if date.today() - timedelta(days=td) <= datetime.strptime(note_last['create_date'], '%Y-%m-%d %H:%M:%S').date():
                    rate += 20.0

            address_ids = self.pool.get('res.partner.address').search(cr, 1, [('partner_id', '=', record['id'])])
            if address_ids:
                flag = True
                for address in self.pool.get('res.partner.address').read(cr, 1, address_ids, ['site_ids', 'phone_ids', 'email_ids', 'name', 'function']):
                    if not (address['name'] and address['name'].strip()) or not (address['function'] and address['function'].strip()):
                        flag = False
                        break

                    site_ids = self.pool.get('res.partner.address.site').search(cr, 1, [('address_id', '=', address['id'])])
                    if site_ids:
                        for item in self.pool.get('res.partner.address.site').read(cr, 1, site_ids, ['name']):
                            if not (item['name'] and item['name'].strip()):
                                flag = False
                                break
                    else:
                        flag = False
                        break

                    phone_ids = self.pool.get('tel.reference').search(cr, 1, [('partner_address_id', '=', address['id'])])
                    if phone_ids:
                        pe = re.compile('^\d+$', re.UNICODE)
                        for item in self.pool.get('tel.reference').read(cr, 1, phone_ids, ['phone']):
                            if not item['phone'] or not pe.match(item['phone']):
                                flag = False
                                break
                    else:
                        flag = False
                        break

                    email_ids = self.pool.get('res.partner.address.email').search(cr, 1, [('address_id', '=', address['id'])])
                    if email_ids:
                        pe = re.compile("^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", re.UNICODE)
                        for item in self.pool.get('res.partner.address.email').read(cr, 1, email_ids, ['name']):
                            if not (item['name'] and pe.match(item['name'])):
                                flag = False
                                break
                    else:
                        flag = False
                        break

                if flag:
                    rate += 5.0
            res[record['id']] = rate
        return res

    def _search_cr_date(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('res.partner.address.site').search(cr, uid, [('name', args[0][1], args[0][2])],
                                                                    context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('site_ids', 'in', site_ids)],
                                                                  context=context)
        partner_ids = self.pool.get('res.partner').search(cr, uid,
                                                          [('address', 'in', address_ids), '|', ('active', '=', False),
                                                           ('active', '!=', False)], context=context)

        if partner_ids:
            return [('id', 'in', partner_ids)]
        return [('id', '=', '0')]

    def _search_site(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('res.partner.address.site').search(cr, uid, [('name', args[0][1], args[0][2])],
                                                                    context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('site_ids', 'in', site_ids)],
                                                                  context=context)
        partner_ids = self.pool.get('res.partner').search(cr, uid,
                                                          [('address', 'in', address_ids), '|', ('active', '=', False),
                                                           ('active', '!=', False)], context=context)

        if partner_ids:
            return [('id', 'in', partner_ids)]
        return [('id', '=', '0')]

    def _search_full_name(self, cr, uid, obj, name, args, context=None):
        rek_ids = self.pool.get('res.partner.bank').search(cr, uid, [('fullname', args[0][1], args[0][2])])
        partner_ids = [b['partner_id'][0] for b in self.pool.get('res.partner.bank').read(cr, uid, rek_ids, ['partner_id']) if b['partner_id']]
        if partner_ids:
            return [('id', 'in', partner_ids)]
        return [('id', '=', '0')]

    def _search_phone(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('tel.reference').search(
            cr,
            uid,
            [
                '|', ('phone', args[0][1], args[0][2]),
                ('phone_for_search', args[0][1], args[0][2])
            ],
            context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('phone_ids', 'in', site_ids)],
                                                                  context=context)
        partner_ids = self.pool.get('res.partner').search(cr, uid,
                                                          [('address', 'in', address_ids), '|', ('active', '=', False),
                                                           ('active', '!=', False)], context=context)

        if partner_ids:
            return [('id', 'in', partner_ids)]
        return [('id', '=', '0')]

    def _search_email(self, cr, uid, obj, name, args, context):
        site_ids = self.pool.get('res.partner.address.email').search(cr, uid, [('name', args[0][1], args[0][2])],
                                                                     context=context)
        address_ids = self.pool.get('res.partner.address').search(cr, uid, [('email_ids', 'in', site_ids)],
                                                                  context=context)
        partner_ids = self.pool.get('res.partner').search(cr, uid,
                                                          [('address', 'in', address_ids), '|', ('active', '=', False),
                                                           ('active', '!=', False)], context=context)

        if partner_ids:
            return [('id', 'in', partner_ids)]
        return [('id', '=', '0')]

    def _search_service(self, cr, uid, obj, name, args, context):
        if args:
            sql = "SELECT partner_id FROM partner_added_services INNER JOIN brief_services_stage ON (brief_services_stage.id = partner_added_services.service_id) WHERE brief_services_stage.service_type = '"+args[0][2]+"';"
            cr.execute(sql)
            res_ids = set(partner_id[0] for partner_id in cr.fetchall())
            if res_ids:
                return [('id', '=', tuple(res_ids))]

    def _search_service_status(self, cr, uid, obj, name, args, context):
        ids = set()
        p_service_pool = self.pool.get('partner.added.services')
        status = ''
        for cond in args:
            status = cond[2]
            break
        if status:
            service_ids = p_service_pool.search(cr, 1, [('partner_id', '!=', False)])
            service_statuses = p_service_pool._get_service_status(cr, 1, service_ids, '', [])
            ids = [k for k, v in service_statuses.iteritems() if get_state(PARTNER_STATUS, status)[1] == v]
            partner_ids = set([r['partner_id'][0] for r in p_service_pool.read(cr, 1, ids, ['partner_id'])])
            if ids:
                return [('id', 'in', tuple(partner_ids))]
        return [('id', '=', '0')]

    def _search_service_name(self, cr, uid, obj, name, args, context):
        service_pool = self.pool.get('partner.added.services')
        services_ids = service_pool.search(cr, 1, [('service_id', '=', args[0][2])])
        partner_ids = set([r['partner_id'][0] for r in service_pool.read(cr, 1, services_ids, ['partner_id']) if r['partner_id']])
        if partner_ids:
            return [('id', 'in', tuple(partner_ids))]
        return [('id', '=', '0')]

    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(r['id'], tools.ustr(self._get_name(r['ur_name'], r['name']))) for r in
                self.read(cr, user, ids, ['ur_name', 'name'], context, load='_classic_write')]

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if args is None:
            args = []
        if context is None:
            context = {}
        args = args[:]
        # optimize out the default criterion of ``ilike ''`` that matches everything
        if not (name == '' and operator == 'ilike'):
            args += ['|', (self._rec_name, operator, name), ('ur_name', operator, name)]
        ids = self._search(cr, user, args, limit=limit, context=context, access_rights_uid=user)
        res = self.name_get(cr, user, ids, context)
        return res

    def _get_partner_status(self, cr, uid, ids, name, arg, context=None):
        service_pool = self.pool.get('brief.services.stage')
        p_service_pool = self.pool.get('partner.added.services')
        res = {}
        for record in self.read(cr, uid, ids, ['added_services_ids'], context):
            process_service_ids = []
            project_service_ids = []
            val = 'new'
            service_ids = [s['service_id'][0] for s in p_service_pool.read(cr, 1, record['added_services_ids'], ['service_id']) if s['service_id']]
            for service in service_pool.read(cr, uid, service_ids, ['service_type']):
                if service['service_type'] == 'process':
                    process_service_ids += p_service_pool.search(cr, 1, [('id', 'in', record['added_services_ids']), ('service_id', '=', service['id'])])
                else:
                    project_service_ids += p_service_pool.search(cr, 1, [('id', 'in', record['added_services_ids']), ('service_id', '=', service['id'])])

            if process_service_ids:
                process_service_status = p_service_pool._get_service_status(cr, 1, process_service_ids, '', []).values()
                if 'Приостановленная' in process_service_status:
                    val = 'paused'
                elif 'Существующая' in process_service_status:
                    val = 'exist'
                elif 'Новая' in process_service_status:
                    val = 'new'
                elif 'Возврат' in process_service_status:
                    val = 'returned'
                elif 'Отказ' in process_service_status:
                    val = 'cancel'

            elif project_service_ids:
                project_service_status = p_service_pool._get_service_status(cr, 1, project_service_ids, '', []).values()
                if 'Существующая' in project_service_status:
                    val = 'exist'
                elif 'Новая' in project_service_status:
                    val = 'new'
                elif 'Закрыт' in project_service_status:
                    val = 'closed'

            res[record['id']] = val
        return res

    def _search_partner_status(self, cr, uid, obj, name, args, context):
        ids = set()
        status = ''
        for cond in args:
            status = cond[2]
            break
        if status:
            partner_ids = self.search(cr, 1, [('lead', '=', False), ('partner_type', '=', 'upsale')])
            #for partner in self.read(cr, 1, partner_ids, ['added_services_ids']):
            partner_statuses = self._get_partner_status(cr, 1, partner_ids, '', [])
            ids = [k for k, v in partner_statuses.iteritems() if get_state(PARTNER_STATUS, status)[0] == v]
        if ids:
            return [('id', 'in', tuple(ids))]
        return [('id', '=', '0')]

    def _check_ppc(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for val in ids:
            added_ids = self.pool.get('partner.added.services').search(cr, 1, [('partner_id', '=', val)])
            services = self.pool.get('partner.added.services').read(cr, 1, added_ids, ['service_id'])
            service_domain = [item['service_id'][0] for item in services if item['service_id']]
            res[val] = False
            if self.pool.get('brief.services.stage').search(cr, 1, [('id', 'in', service_domain), ('direction', '=', 'PPC')], count=True):
                res[val] = True
        return res

    def _main_name(self, cr, uid, ids, field, arg, context):
        res = {}
        for i in self.read(cr, 1, ids, ['address']):
            name = ''
            phone = ''
            site = ''
            address_ids = self.pool.get('res.partner.address').search(cr, 1, [('main_face', '=', True), ('id', 'in', i['address'])])

            if address_ids:
                address = self.pool.get('res.partner.address').read(cr, uid, address_ids[0], ['name', 'phone_ids', 'email_ids'])

                name = address['name']
                if address['email_ids']:
                    site_name = self.pool.get('res.partner.address.email').read(cr, uid, address['email_ids'][0], ['name'])
                    site = site_name['name']
                if address['phone_ids']:
                    phone_name = self.pool.get('tel.reference').read(cr, uid, address['phone_ids'][0], ['phone'])
                    phone = phone_name['phone']

            res[i['id']] = {
                'partner_name': name,
                'phone_default': phone,
                'email_default': site
            }
        return res

    _columns = {
        'name': fields.char('Партнер (основной сайт)', size=250),
        'ur_name': fields.char('Юридическое название компании', size=250, help='Юридическое название компании'),
        'partner_base': fields.selection(
            (
                ('hot', 'Теплая БД'),
                ('cold', 'Холодная БД'),
            ), 'Тип БД'
        ),

        'provider_category': fields.many2one(
            'res.provider.category',
            'Категория поставщка',
            select=True,
            help='Категория - выпадающий список. Поле заполняется менеджером'
        ),
        'section_id': fields.many2one(
            'crm.case.section',
            'Отдел продаж',
            help='Направление, которому принадлежит Партнер'
        ),
        'reference': fields.char('Ссылка на сайт', size=64),
        'partner_type': fields.selection(
            [
                ('inksystem', 'INKSYSTEM'),
                ('contact', 'Контакт-центр'),
                ('upsale', 'UpSale'),
                ('eu', 'ЕС')
            ], 'Кандидат компании'),
        'phone_ids': fields.one2many('tel.reference', 'partner_address_id', 'Номера телефонов'),
        'orders_history': fields.one2many('partner.order.history', 'partner_id', 'История заказов'),
        'section_id_sales': fields.many2one('crm.case.section', 'Отдел продаж'),
        'dealer_discount': fields.one2many('partner.dealer.discount', 'partner_id', 'Дилерская скидка'),
        'confirm_status': fields.selection([('yes', 'Да'), ('no', 'Нет')], 'Наличие статус'),
        'login': fields.char('Логин', size=250),
        'password': fields.char('Пароль', size=250),
        'forward_to': fields.char('Переадресация на', size=250),
        'main_partner': fields.many2one('res.partner', 'Головной партнер'),
        'admin_panel_login': fields.char('Логин админпанели', size=250),
        'admin_panel_password': fields.char('Пароль админпанели', size=250),
        'corporate_site_url': fields.char('Адрес сайта', size=250),

        'corporate_admin_panel': fields.char('Админпанель сайта', size=250),
        'corporate_admin_password': fields.char('Пароль админпанели сайта', size=250),
        'next_call': fields.datetime('Следующий звонок', help='Дата следующего контакта.'),
        'partner_status': fields.function(
            _get_partner_status,
            fnct_search=_search_partner_status,
            type='selection',
            selection=PARTNER_STATUS,
            string='Статус партнера',
            help='Этап работы с партнером. Поле заполняется менеджером'
        ),
        'services_ids': fields.one2many(
            'crm.services.rel.stage',
            'partner_id',
            'Услуги',
            help='Таблица заполняется менеджером продаж'
        ),

        'invoice_ids': fields.one2many(
            'account.invoice',
            'partner_id',
            'Счета',
            domain=[('type', '=', 'out_invoice')]
        ),
        'zds_ids': fields.one2many(
            'account.invoice',
            'partner_id',
            'ЗДС',
            domain=[('type', '=', 'in_invoice')]
        ),

        'added_services_ids': fields.one2many(
            'partner.added.services',
            'partner_id',
            'Подключенные услуги',
            help='Таблица подключенных услуг.'
        ),
        'added_services_history_ids': fields.one2many(
            'partner.added.services.history',
            'partner_id',
            'Подключенные услуги (История)',
            help='Таблица истории подключенных услуг.'
        ),
        'added_services_history_change_ids': fields.one2many(
            'partner.added.services.change.history',
            'partner_id',
            'История изменений',
            help='Таблица истории подключенных услуг.'
        ),
        'operation_deps': fields.one2many('partner.operational.departments', 'partner_id', 'Операционные направления'),
        'bonus_amount': fields.float('Сумма бонуса', help='Сумма бонуса'),
        'bonus_reason': fields.many2one('partner.bonus.reason', 'Причина бонуса', help='Причина бонуса'),
        'rebate_system': fields.selection(
            [
                ('yes', 'Да'),
                ('no', 'Нет')
            ], 'Наличие системы Rebate'
        ),
        'bonus_friend': fields.selection(
            [
                ('yes', 'Да'),
                ('no', 'Нет')
            ],
            'Бонусная программа "Приведи друга"',
            help='Заполняется в случае участия Партнера в Бонусной программе'),
        'refusion_reason': fields.many2one('partner.refusion.reason', 'Причина отказа'),
        'refusion_description': fields.text(
            'Причина отказа',
            help='Причина по которой Партнер отказался.',
        ),
        #'emails': fields.one2many('mailgate.message', 'partner_id', 'Emails', readonly=True),
        'note_ids': fields.one2many(
            'crm.lead.notes',
            'partner_id',
            'Заметки',
            domain=[('type', '!=', 'skk')],
            help='Поле для внесения комментариев',
        ),
        'skk_note_ids': fields.one2many(
            'crm.lead.notes',
            'partner_id',
            'Заметки для СКК',
            domain=[('type', '=', 'skk')],
            help='Поле для внесения комментариев'
        ),
        'activity': fields.char('Сфера деятельности', size=250),
        'cand_type': fields.selection([('pers', 'Частное лицо'), ('firm', 'Фирма')], 'Тип партнера'),
        'sale_type': fields.selection([('w', 'Опт'), ('r', 'Розница')], 'Тип продаж'),
        'comm_ids': fields.one2many('crm.communication.history', 'partner_id', string="История общения"),
        'source': fields.many2one('crm.source.stage', 'Источник'),
        'author_id': fields.many2one('res.users', 'Автор', readonly=True),
        'price_type': fields.selection(
            [
                ('retail', 'Розница'),
                ('c_eur', 'C-EUR'),
                ('d_eur', 'D-EUR'),
                ('c_usd', 'C-USD'),
                ('d_usd', 'D-USD'),
                ('percent', '%')
            ], 'Тип цены'),
        'pay_notes': fields.text('Примечания об оплате'),
        'partner_state': fields.many2one('partner.partner.state', 'Статус партнера'),
        'pay_type': fields.many2one('partner.pay.type', 'Способ оплаты'),
        'delivery_type': fields.many2one('partner.delivery.type', 'Способ доставки'),
        'pay_type_ec': fields.many2many(
            'partner.pay.type',
            'partner_pay_type_rel',
            'part_id',
            'pay_id',
            'Способ оплаты'),
        'delivery_type_ec': fields.many2many(
            'partner.delivery.type',
            'partner_delivery_type_rel',
            'part_id',
            'delivery_id',
            'Способ доставки'),
        'id_vat': fields.char('ID_VAT', size=128),
        'delivery_from': fields.many2one('partner.delivery.from', 'Откуда делается доставка'),
        'budget': fields.float('Бюджет'),
        'product_id': fields.one2many('crm.patner.product', 'res_partner', string="Товары"),
        'write_date': fields.datetime('Последняя дата контакта', readonly=True),

        'partner_name': fields.function(_main_name, type="char", method=True, string='Имя контакта', multi='address'),

        'circulation': fields.one2many('res.partner.circulation', 'partner_id', 'Оборот партнера в $'),
        'has_eshop': fields.selection(
            [
                ('yes', 'Есть'),
                ('no', 'Нет')
            ], 'Интернет-магазин'),
        'what_done': fields.text('Что сделано для продвижения магазина'),


        'partner_site_default': fields.related('address', 'site_ids', 'name', type='char', string='Сайт партнера'),
        'phone_default': fields.function(_main_name, type="char", method=True, string='Телефон', multi='address'),
        'email_default': fields.function(_main_name, type="char", method=True, string='Эл. почта', multi='address'),

        'last_circulation': fields.function(_last_circulation, type="float", method=True),
        'fin_dog': fields.selection(
            [
                ('iys', 'Исключительные условия сотрудничества'),
                ('sssppvsyad', 'Сохранение существующей скидки потенциального партнера в системе Яндекс.Директ'),
                ('sr', 'Система Rebate'),
                ('bdyw', 'Бонус для участников вебинара'),
                ('cc', 'Клубная карта')
            ], 'Финансовые договоренности', help='Финансовые договоренности с Партнером'),
        'categ_id': fields.many2one(
            'crm.case.categ',
            'Тематика',
            #domain="['|', ('section_id', '=', False), ('responsible_users', '=', user_id)]",
            help='Категория, которой принадлежит данный Партнер'
        ),

        'access_ids': fields.one2many(
            'res.partner.access',
            'partner_id',
            'Доступы, предоставляемые партнером',
            help='Таблица заполняется менеджером продаж. Вносятся доступы к админпанеле, серверу и т.д.'
        ),
        'transfer_ids': fields.one2many('transfer.history', 'partner_id', 'История переприсвоения'),

        #  Критерии
        'terms_of_service': fields.char('Сроки предоставления услуги', size=10),
        'conformity': fields.char('Соответствие услуги всем входным требованиям, указанным в ТЗ', size=10),
        'quality_feedback': fields.char(
            'Качество обратной связи с представителем Компании , скорость и полнота ответов менеджера', size=10),
        'completeness_of_reporting': fields.char(
            'Полнота отчетов о результатах рекламной кампании и соблюдение сроков их предоставления', size=10),

        'client_type': fields.selection(
            [
                ('agent', 'агент'),
                ('diler', 'дилер'),
                ('distributor', 'дистрибутор'),
                ('retail', 'retail'),
                ('vip-r', 'VIP-R (VIP-retail)'),
                ('nks', 'НКС (нетрадиционные каналы сбыта)'),
            ], 'Категория клиента'
        ),

        'check': fields.function(_check_access, type="boolean", method=True, string='Проверка'),
        'service': fields.function(
            _get_service,
            type="many2one",
            relation='brief.services.stage',
            string='Услуга',
            method=True,
            fnct_search=_search_service_name
        ),
        'site_s': fields.function(
            lambda *a: dict((r_id, '') for r_id in a[3]),
            method=True,
            string='Сайт',
            type='char',
            fnct_search=_search_site
        ),

        'next_call_comment': fields.char(
            'Комментарий к следующему звонку',
            size=250,
            help='Комментарий к следующему звонку'),
        'stage_id': fields.many2one(
            'crm.case.stage',
            'Этап',
            domain="[('section_ids', '=', section_id)]",
            help='Этап Кандидата'),
        'priority': fields.selection(AVAILABLE_PRIORITIES, 'Приоритет', select=True, help='Приоритет Кандидата'),
        'lead': fields.boolean('Кандидат'),
        'last_comment': fields.related('note_ids', 'title', type='char', size=128, string='Комментарий'),

        'phone_s': fields.function(
            lambda *a: dict((r_id, '') for r_id in a[3]),
            method=True,
            string='Телефон',
            type='char',
            fnct_search=_search_phone
        ),

        'email_s': fields.function(
            lambda *a: dict((r_id, '') for r_id in a[3]),
            method=True,
            string='Эл. почта',
            type='char',
            fnct_search=_search_email
        ),
        'full_name_s': fields.function(
            lambda *a: dict((r_id, '') for r_id in a[3]),
            method=True,
            string='Полное наименование партнера',
            type='char',
            size=250,
            fnct_search=_search_full_name
        ),

        'service_s': fields.function(
            lambda *a: dict((r_id, '') for r_id in a[3]),
            method=True,
            string='Тип услуги',
            type='selection',
            selection=SERVISE_TYPE,
            fnct_search=_search_service
        ),
        'service_status': fields.function(
            lambda *a: dict((r_id, '') for r_id in a[3]),
            method=True,
            string='Статус услуги',
            type='selection',
            selection=PARTNER_STATUS,
            fnct_search=_search_service_status
        ),



        'date_start_from': fields.date('дата начала с'),
        'date_start_to': fields.date('дата начала по'),
        'date_finish_from': fields.date('дата окончания с'),
        'date_finish_to': fields.date('дата окончания с'),

        'create_date': fields.datetime(
            'Дата создания',
            select=True,
            readonly=True,
            help='Дата создания кандидата.'),

        'status_history_ids': fields.one2many('res.partner.status.history', 'partner_id', 'История смены статусов'),
        'attachment_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Вложения',
            domain=[('res_model', '=', 'res.partner')],
            context={'res_model': 'res.partner'}
        ),

        'process_ids': fields.one2many('process.launch', 'partner_id', 'Процессы'),
        'report_payment_ids': fields.function(
            _get_report_payment,
            type="one2many",
            relation="invoice.reporting.period",
            store=False,
            readonly=True,
            string="Суммы за период"
        ),
        'discounts_ids': fields.one2many('res.partner.ppc.discounts', 'partner_id', 'Скидки', domain=['|', ('finish_date', '>=', date.today().strftime('%Y-%m-%d')), ('permanent', '=', True)]),
        'discounts_history_ids': fields.one2many('res.partner.ppc.discounts.history', 'partner_id', 'Скидки'),
        'check_ppc': fields.function(_check_ppc, type="boolean", method=True, string="Маркер PPC"),
        'old_discounts_ids': fields.one2many('res.partner.ppc.discounts', 'partner_id', 'Скидки', domain=[('finish_date', '<', date.today().strftime('%Y-%m-%d'))]),
        'control_ids': fields.one2many('res.partner.quality.control', 'partner_id', 'Управление качеством'),

        'description': fields.text('Описание компании', help='-специфика работы;\n-на чем они зарабатывают больше всего;\n-ключевые направления деятельность;\n-специфика иерархии в компании;\n-основные векторы дальнейшего развития и тд.'),
        'key_person': fields.text('Характеристика ключевых лиц', help='должности, эмоциональные характеристики, их интересы и другие важные данные для работы с ними'),
        'zone': fields.text('Зоны ответственности разных контактных лиц', help='Кто за что отвечает'),
        'key_moment': fields.text('Ключевые моменты взаимодействия нашей компании и партнера', help='Например, партнер приезжал к нам в Харьков, конфликты с партнером и тд.'),
        'another': fields.text('Другое, Способ оплаты(тип оплаты, сумма, разбивка, частота)', help='Любая другая полезная информация'),

        'rate': fields.function(
            _get_rate,
            type='float',
            readonly=True,
            digits=(3, 2),
            string='Процент заполненности'
        )
    }

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        lead = context.get('lead', True)
        return lead

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'section_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid,
                                                                                       context).context_section_id.id,
        'partner_status': 'new',
        'author_id': lambda self, cr, uid, context: uid,
        'lead': _get_type,
        'partner_base': 'cold',
    }

    def add_note(self, cr, uid, ids, context=None):
        view_id = self.pool.get('ir.ui.view').search(cr, uid,
                                                     [('name', 'like', 'CRM Note'), ('model', '=', self._name)])

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead.notes',
            'name': 'Добавление заметки',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': {
                'partner_id': ids[0],
            },
            'target': 'new',
            'nodestroy': True,
        }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=None):
        date_indx = []
        date_st_to = None
        date_fn_to = None
        date_st_from = None
        date_fn_from = None
        sql_postfix = []

        obj_tel = self.pool.get('tel.reference')
        get_id = False
        for indx, item in enumerate(args):
            if 'date_start_from' == item[0]:
                date_st_from = item[2]
                date_indx.append(indx)
            if 'date_start_to' == item[0]:
                date_st_to = item[2]
                date_indx.append(indx)
            if 'date_finish_to' == item[0]:
                date_fn_to = item[2]
                date_indx.append(indx)
            if 'date_finish_from' == item[0]:
                date_fn_from = item[2]
                date_indx.append(indx)

            if 'phone_ids' in item:
                args.pop(indx)
                search_ids = obj_tel.search(
                    cr,
                    uid,
                    [
                        ('phone_for_search', 'ilike', item[2]),
                        ('res_partner_id', '!=', False)
                    ])
                res = obj_tel.read(cr, uid, search_ids, ['res_partner_id'])
                it_d = [item['res_partner_id'][0] for item in res]
                args.append(('id', 'in', it_d))

        if date_st_from is not None and date_st_to is None:
            sql_postfix.append("date_start='{0}'::date".format(date_st_from,))
        elif date_st_from is not None and date_st_to is not None:
            sql_postfix.append("date_start between '{0}'::date and '{1}'::date".format(date_st_from, date_st_to))

        if date_fn_from is not None and date_fn_to is None:
            sql_postfix.append("date_finish='{0}'::date".format(date_fn_from,))
        elif date_fn_from is not None and date_fn_to is not None:
            sql_postfix.append("date_finish between '{0}'::date and '{1}'::date".format(date_fn_from, date_fn_to))

        sql_postfix_str = ' AND '.join(sql_postfix)
        if sql_postfix_str:
            sql1 = 'SELECT partner_id FROM partner_added_services WHERE {0}'.format(sql_postfix_str,)
            sql2 = 'SELECT partner_id FROM partner_added_services_history WHERE {0}'.format(sql_postfix_str,)

            cr.execute(sql1)
            res_ids1 = set(partner_id[0] for partner_id in cr.fetchall())
            cr.execute(sql2)
            res_ids2 = set(partner_id[0] for partner_id in cr.fetchall())
            res_ids = res_ids1 | res_ids2
            args.append(['id', 'in', tuple(res_ids)])

        if date_indx:
            date_indx.sort()
            date_indx.reverse()
            for indx in date_indx:
                del args[indx]

        return super(ResPartner, self).search(cr, uid, args, offset, limit, order, context, count)

    def write(self, cr, user, ids, vals, context=None):
        next_partner_status = vals.get('partner_status', False)
        for record in self.read(cr, user, ids, ['partner_status', 'address', 'name']):
            partner_status = record['partner_status']
            address = record['address']
            if address:
                res_partner_address_site = self.pool.get('res.partner.address.site')
                if not res_partner_address_site.search(cr, user, [('name', '=', record['name'])]):
                    res_partner_address_site.create(cr, user, {'address_id': address[0], 'name': record['name']})

            if partner_status and next_partner_status and partner_status != next_partner_status:
                vals.update({'status_history_ids': [(0, 0, {'name': next_partner_status})]})

        if vals.get('stage_id', False) and vals['stage_id'] == 41 and not vals.get('refusion_description', False):
            raise osv.except_osv('Кандидат', 'Необходимо заполнить "Причину отказа"')

        for attachment in vals.get('attachment_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'res.partner'

        return super(ResPartner, self).write(cr, user, ids, vals, context)

    def create(self, cr, user, vals, context=None):
        categ_ids = self.pool.get('crm.case.categ').search(cr, user, [('responsible_users', '=', user)])
        if vals.get('partner_base') == 'cold' and (not vals.get('categ_id') or vals['categ_id'] not in categ_ids):
            raise osv.except_osv("Ошибка", "Заполните поле 'Тематика' Вашей тематикой")
        return super(ResPartner, self).create(cr, user, vals, context)

    def _check_unique_insesitive(self, cr, uid, ids, context=None):
        for self_obj in self.browse(cr, 1, ids, context):
            if self.search(cr, 1, [('name', '=', self_obj.name), ('id', '!=', self_obj.id)], context):
                return False
            return True

    def _check_unique_lead(self, cr, uid, ids, context=None):
        sr_ids = self.pool.get('crm.lead').search(cr, 1, [], context)
        lst = [
            x.name.lower()
            for x in self.pool.get('crm.lead').browse(cr, 1, sr_ids, context=context)
            if x.name
        ]
        for self_obj in self.browse(cr, 1, ids, context=context):
            list_sites = [x.name.lower() for address in self_obj.address for x in address.site_ids]
            if [x for site_p in list_sites if site_p in lst] and not self_obj.opportunity_ids:
                return False
            return True

    def _check_criteries(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids):
            terms_of_service = record.terms_of_service or 0
            conformity = record.conformity or 0
            quality_feedback = record.quality_feedback or 0
            completeness_of_reporting = record.completeness_of_reporting or 0
            if (record.partner_type in ('upsale', False) and terms_of_service \
                    and conformity and quality_feedback and completeness_of_reporting):

                try:
                    sum_criteries = int(terms_of_service) + int(conformity) + \
                                    int(quality_feedback) + int(completeness_of_reporting)
                except:
                    sum_criteries = 0

                if sum_criteries != 100:
                    return False
        return True

    def _check_unique_phone(self, cr, uid, ids, context=None):
        for self_obj in self.browse(cr, 1, ids, context):
            address_ids = [item.id for item in self_obj.address]
            for addr in self_obj.address:
                for phone in addr.phone_ids:
                    domain = [
                        ('partner_address_id', 'not in', address_ids),
                        'partner_id', '!=', False,
                        '|', ('phone', '=', phone.phone),
                        '|', ('phone', '=', phone.phone_for_search),
                        '|', ('phone_for_search', '=', phone.phone),
                        ('phone_for_search', '=', phone.phone_for_search)
                    ]
                    if self.pool.get('tel.reference').search(cr, 1, domain, context):
                        return False
            return True

    def _check_contact_full(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, ['address', 'partner_base']):
            if record['partner_base'] == 'hot':
                if not record['address']:
                    return False
        return True

    def _check_service_full(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, ['added_services_ids', 'partner_base']):
            if record['partner_base'] == 'hot':
                if not record['added_services_ids']:
                    return False
        return True

    def _check_note_full(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, ['note_ids', 'partner_base']):
            if record['partner_base'] == 'hot' and not record['note_ids']:
                return False
        return True

    def to_partner(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for obj in self.browse(cr, uid, ids, context=context):
            if not obj.ur_name:
                raise osv.except_osv("Кандидат", "Заполните 'Юридическое название компании'")
            self.write(cr, uid, [obj.id], {'lead': False, 'partner_status': 'new'})

        view_id = self.pool.get('ir.ui.view').search(
            cr,
            uid,
            [
                ('name', 'like', 'res.partner.form upsale'),
                ('model', '=', self._name)
            ])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'views': [(view_id[0], 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
            'res_id': ids[0],
        }

    _constraints = [
        (
            _check_unique_insesitive,
            'должен быть уникальным!',
            [u'Основной сайт']
        ),
        (
            _check_contact_full,
            'Контакт должен быть указан!',
            [u'Контакт']
        ),
        #(
        #    _check_note_full,
        #    'Журнал должен быть заполнен!',
        #    [u'Журнал']
        #),
        (
            _check_service_full,
            'Услуга должена быть указана!',
            [u'Услуга']
        ),
        (
            _check_criteries,
            'Сумма критериев должна равняться 100 и не должно быть пустых полей',
            []
        ),
        #(
        #    _check_unique_phone,
        #    'Уже создан Кандидат/Партнер с таким номером телефона',
        #    []
        #),
    ]
ResPartner()


class TransferHistory(Model):
    _name = 'transfer.history'
    _description = u'Lead/Partner - История переприсвоение карточки'
    _log_create = True
    _order = "create_date desc"

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'user_id': fields.many2one('res.users', 'Перевел', readonly=True),
        'name': fields.many2one('res.users', 'На кого переприсвоили'),
        'create_date': fields.datetime('Дата', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', invisible=True),
    }
TransferHistory()


class PartnerStatusHistory(Model):
    _name = 'res.partner.status.history'
    _description = u'Partner - История изменения статуса партнера'
    _log_create = True
    _order = "create_date desc"

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'name': fields.selection(
            [
                ('new', 'Новый'),
                ('existing', 'Существующий'),
                ('stoped', 'Приостановлен'),
                ('refusion', 'Отказ')
            ], 'На какой статус'),
        'create_date': fields.datetime('Дата', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', invisible=True),
    }
PartnerStatusHistory()


class PartnerPpcDiscounts(Model):
    """
    модель скидок для партнера и кандидата
    """
    _name = 'res.partner.ppc.discounts'
    _description = u'Скидки'
    _columns = {
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'discount_type': fields.selection(
            [
                ('yandex_discount', 'Скидка Up в аккаунте Яндекс'),
                ('google_discount', 'Скидка Up в аккаунте Google'),
                ('partner_discount', 'Скидка Партнера'),
                ('nds', 'НДС')
            ], 'Тип скидки', required=True),
        'percent': fields.float('Значение'),
        'google': fields.boolean('4500'),
        'start_date': fields.date('Дата начала'),
        'finish_date': fields.date('Дата окончания'),
        'permanent': fields.boolean('На постоянной основе'),
        'create_uid': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата', readonly=True),
        'old_percent': fields.float('старое значение'),
        'history_ids': fields.one2many('res.partner.ppc.discounts.history', 'discount_id', string='История')
    }

    _defaults = {
        'partner_id': lambda self, cr, uid, context: context.get('partner_id', False),
        'discount_type': 'nds',
    }

    def change_partner_id(self, cr, uid, ids, partner_id):
        service_domain = []
        if partner_id:
            added_ids = self.pool.get('partner.added.services').search(cr, 1, [('partner_id', '=', partner_id)])
            services = self.pool.get('partner.added.services').read(cr, 1, added_ids, ['service_id'])
            service_domain = [item['service_id'][0] for item in services if item['service_id']]
        return {'domain': {'service_id': [('id', 'in', service_domain), ('direction', '=', 'PPC')]}}

    def onchange_google(self, cr, uid, ids, google, percent, old_percent=0.0):
        if google:
            return {'value': {'percent': 4500, 'old_percent': percent}}
        else:
            return {'value': {'percent': old_percent, 'old_percent': 4500}}

    def create(self, cr, user, vals, context=None):
        if vals.get('google', False):
            vals['percent'] = 4500.0
        return super(PartnerPpcDiscounts, self).create(cr, user, vals, context)

    def write(self, cr, user, ids, vals, context=None):
        if vals.get('google', False):
            vals['percent'] = 4500.0
        if vals.get('permanent', False):
            vals['start_date'] = None
            vals['finish_date'] = None

        for record in self.read(cr, user, ids, ['partner_id', 'service_id', 'discount_type', 'percent', 'google', 'start_date', 'finish_date', 'permanent']):
            if vals.get('service_id') or vals.get('discount_type') or vals.get('percent') or vals.get('google') or vals.get('finish_date') or vals.get('start_date') or vals.get('permanent'):
                new_permanent = record['permanent']
                if 'permanent' in vals.keys():
                    new_permanent = vals['permanent']

                new_google = record['google']
                if 'google' in vals.keys():
                    new_google = vals['google']

                vals.update({'history_ids': [(0, 0, {
                    'partner_id': record['partner_id'][0],
                    'service_id': vals.get('service_id') or record['service_id'][0],
                    'old_service_id': record['service_id'][0],

                    'discount_type': vals.get('discount_type') or record['discount_type'],
                    'old_discount_type': record['discount_type'],

                    'percent': vals.get('percent') or record['percent'],
                    'old_percent': record['percent'],

                    'google': new_google,
                    'old_google': record['google'],

                    'start_date': vals.get('start_date') or record['start_date'],
                    'old_start_date': record['start_date'],

                    'finish_date': vals.get('finish_date') or record['finish_date'],
                    'old_finish_date': record['finish_date'],

                    'permanent': new_permanent,
                    'old_permanent': record['permanent'],
                })]})
        return super(PartnerPpcDiscounts, self).write(cr, user, ids, vals, context)
PartnerPpcDiscounts()


class PartnerPpcDiscountsHistory(Model):
    _name = 'res.partner.ppc.discounts.history'
    _description = 'История скидок'
    _columns = {
        'discount_id': fields.many2one('res.partner.ppc.discounts'),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'discount_type': fields.selection(
            [
                ('yandex_discount', 'Скидка Up в аккаунте Яндекс'),
                ('google_discount', 'Скидка Up в аккаунте Google'),
                ('partner_discount', 'Скидка Партнера'),
                ('nds', 'НДС')
            ], 'Тип скидки', required=True),
        'percent': fields.float('Значение'),
        'google': fields.boolean('4500'),
        'start_date': fields.date('Дата начала'),
        'finish_date': fields.date('Дата окончания'),
        'permanent': fields.boolean('На постоянной основе'),
        'create_uid': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата', readonly=True),
        'old_service_id': fields.many2one('brief.services.stage', 'Предидущее Услуга'),
        'old_discount_type': fields.selection(
            [
                ('yandex_discount', 'Скидка Up в аккаунте Яндекс'),
                ('google_discount', 'Скидка Up в аккаунте Google'),
                ('partner_discount', 'Скидка Партнера'),
                ('nds', 'НДС')
            ], 'Предидущий Тип скидки', required=True),
        'old_percent': fields.float('Предидущее Значение'),
        'old_google': fields.boolean('Предидущее 4500'),
        'old_start_date': fields.date('Предидущая Дата начала'),
        'old_finish_date': fields.date('Предидущая Дата окончания'),
        'old_permanent': fields.boolean('Предидущее На постоянной основе'),
    }
PartnerPpcDiscountsHistory()


class PartnerQualityControl(Model):
    _name = 'res.partner.quality.control'
    _description = u'Управление качеством'
    _rec_name = 'period_id'

    def change_ydolit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'Управление качеством'), ('model', '=', self._name), ('type', '=', 'form')])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'name': 'Управление качеством',
            'view_id': view_id,
            'res_id': ids[0] or 0,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
            'context': {'add': True},
        }

    def save(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def _get_ydolit(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for record in self.read(cr, uid, ids, ['partner_id', 'criteria_ids', 'period_id', 'service_id'], context=context):
            res[record['id']] = {
                'level_ydolit': 0.0,
                'index_ydolit': 0.0,
                'mbo': 0.0
            }
            partner = self.pool.get('res.partner').read(cr, 1, record['partner_id'][0], ['terms_of_service', 'conformity', 'quality_feedback', 'completeness_of_reporting'])
            level = sum(c['value']*float(partner[c['name']])/100 for c in self.pool.get('res.partner.quality.criteria').read(cr, 1, record['criteria_ids'], ['name', 'value']))

            if record['partner_id'] and record['service_id']:
                process_launch_ids = self.pool.get('process.launch').search(cr, 1, [('partner_id', '=', record['partner_id'][0]), ('service_id', '=', record['service_id'][0])])
                if process_launch_ids:
                    data = self.pool.get('process.launch').read(cr, 1, process_launch_ids,  ['process_model', 'process_id'])
                    if data:
                        sla_ids = self.pool.get('process.sla').search(cr, 1, [('process_model', '=', data[0]['process_model']), ('process_id', '=', data[0]['process_id']), ('period_id', '=', record['period_id'][0])])
                        if sla_ids:
                            mbo_list = self.pool.get('process.sla').read(cr, 1, sla_ids[0], ['avg_mbo'])
                            res[record['id']]['mbo'] = mbo_list['avg_mbo']

            res[record['id']]['level_ydolit'] = level
            res[record['id']]['index_ydolit'] = numpy.mean((level, res[record['id']]['mbo'])) if res[record['id']]['mbo'] else level

        return res

    _columns = {
        'period_id': fields.many2one(
            'kpi.period',
            'Период',
            domain=[('calendar', '=', 'rus')]
        ),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'date_call': fields.datetime('Дата прозвона'),
        'create_uid': fields.many2one('res.users', 'Специалист по упр. качеством', readonly=True),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'direction': fields.related(
            'service_id',
            'direction',
            string='Направление',
            type='char',
            size=10,
            store=True,
        ),
        'specialist_id': fields.many2one('res.users', 'Специалист', readonly=True),
        'criteria_ids': fields.one2many('res.partner.quality.criteria', 'quality_id', string='Критерии'),
        'mbo': fields.function(
            _get_ydolit,
            type='float',
            string='MBO',
            multi='ydolit',
            readonly=True,
        ),
        # Троллинг Маши Кравчук за "Уровень удолит." в ТЗ
        'level_ydolit': fields.function(
            _get_ydolit,
            type='float',
            string='Уровень удовлетворенности',
            multi='ydolit',
            readonly=True,
        ),
        'index_ydolit': fields.function(
            _get_ydolit,
            type='float',
            string='Индекс удовлетворенности',
            multi='ydolit',
            readonly=True,
        ),
    }

    def _check_unique(self, cr, uid, ids, context=None):
        for self_obj in self.read(cr, 1, ids, ['period_id', 'service_id', 'partner_id'], context):
            if self.search(cr, 1, [('period_id', '=', self_obj['period_id'][0]), ('service_id', '=', self_obj['service_id'][0]), ('id', '!=', self_obj['id']), ('partner_id', '=', self_obj['partner_id'][0])], context):
                return False
            return True

    _constraints = [
        (
            _check_unique,
            'оценивать одну и ту же услугу 2 раза за период!',
            [u'Нельзя']
        ),
    ]
PartnerQualityControl()


class PartnerQualityCriteria(Model):
    _name = 'res.partner.quality.criteria'
    _description = u'Управление качеством - Критерии'

    _columns = {
        'name': fields.selection(
            CRITERIAS, 'Критерий'
        ),
        'value': fields.float('Оценка'),
        'comment': fields.text('Комментарий'),
        'quality_id': fields.many2one('res.partner.quality.control', 'Управление качеством'),
    }
PartnerQualityCriteria()


class InvoiceReportingPeriod(Model):
    _name = 'invoice.reporting.period'
    _order = 'period_name desc'
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'payment_sum': fields.float('Сумма платежей, $'),
        'period_name': fields.related(
            'period_id',
            'name',
            type='char',
            size=7,
            store=True
        ),
    }
InvoiceReportingPeriod()
