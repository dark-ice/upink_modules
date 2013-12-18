# -*- coding: utf-8 -*-
from __future__ import print_function, division
import decimal_precision as dp
from datetime import date
from openerp import netsvc
from openerp.osv import fields, osv
from openerp.osv.orm import Model

from notify import notify

wf_service = netsvc.LocalService("workflow")


class AccountInvoice(Model):
    _inherit = 'account.invoice'
    _rec_name = 'number'

    _states = (
        ('draft', 'Черновик'),
        ('open', 'Счет выставлен'),
        ('confirm', 'Утверждение'),
        ('proforma', 'Частично оплачено'),
        ('proforma2', 'Проведение оплаты'),
        ('paid', 'Оплачен полностью'),
        ('close', 'ЗДС закрыто'),
        ('cancel', 'Отмена')
    )

    def get_state(self, state):
        return [item for item in self._states if item[0] == state][0]

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'untaxed': 0.0,
                'a_tax': 0.0,
                'a_total': 0.0
            }
            for line in invoice.invoice_line:
                res[invoice.id]['a_total'] += line.price_currency
            tax = 0.0
            if invoice.account_id:
                tax = invoice.account_id.tax / 100

            res[invoice.id]['untaxed'] = res[invoice.id]['a_total'] / (1 + tax)
            res[invoice.id]['a_tax'] = res[invoice.id]['a_total'] - res[invoice.id]['untaxed']
        return res

    def _get_rate(self, cr, uid, ids, name, arg, context=None):
        res = {}
        currency_rate_pool = self.pool.get('res.currency.rate')
        currency_pool = self.pool.get('res.currency')
        for record in self.browse(cr, uid, ids):
            currency_date_ids = currency_rate_pool.search(
                cr,
                uid,
                [('name', '=', record.date_invoice), ('currency_id', '=', record.currency_id.id)]
            )
            if currency_date_ids:
                currency = currency_rate_pool.read(cr, uid, currency_date_ids[0], ['rate'])
            else:
                currency = currency_pool.read(cr, uid, record.currency_id.id, ['rate'])
            res[record.id] = currency['rate']
        return res

    def onchange_account(self, cr, uid, ids, account_id, context=None):
        account_pool = self.pool.get('account.account')
        account_obj = account_pool.read(cr, uid, account_id, ['currency_id', 'tax', 'lang'])
        return {
            'value': {'currency_id': account_obj['currency_id'], 'tax': account_obj['tax'], 'lang': account_obj['lang']}}

    def onchange_bank(self, cr, uid, ids, partner_id, lead_id, context=None):
        if partner_id:
            domain = [('partner_id.id', '=', partner_id)]
        elif lead_id:
            domain = [('lead_id.id', '=', lead_id)]
        else:
            domain = []

        return {'domain': {'bank_id': domain}}

    def onchange_currency(self, cr, uid, ids, date, currency_id, context=None):
        if currency_id is not None and currency_id:
            currency_rate_pool = self.pool.get('res.currency.rate')
            currency_pool = self.pool.get('res.currency')
            currency_date_ids = currency_rate_pool.search(cr, uid,
                                                          [('name', '=', date), ('currency_id', '=', currency_id)])
            if currency_date_ids:
                currency_date = currency_rate_pool.read(cr, uid, currency_date_ids[0], ['rate'])
            else:
                currency_date = currency_pool.read(cr, uid, currency_id, ['rate'])
            return {'value': {'rate': currency_date['rate']}}

    def change_card(self, cr, uid, ids, card_id, context=None):
        if card_id is not None and card_id:
            account_pool = self.pool.get('account.invoice.card')
            account_obj = account_pool.browse(cr, uid, card_id)
            if account_obj and account_obj.currency_id:
                return {'value': {'currency_id': account_obj.currency_id.id}}
        return {'value': {'currency_id': None}}

    def change_type(self, cr, uid, ids, card_id, context=None):
        return {'value': {'card_id': None}}

    def change_division(self, cr, uid, ids, division_id, context=None):
        obj = self.pool.get('account.invoice.division').read(cr, uid, division_id, ['division'])
        return {
            'value': {
                'get_division': obj['division']
            },
            'domain': {
                'categ_id': [('division_id', '=', division_id)]
            }
        }

    def change_bank(self, cr, uid, ids, bank_id, context=None):
        account_pool = self.pool.get('res.partner.bank')
        account_obj = account_pool.browse(cr, uid, bank_id)
        return {'value': {'full_name': account_obj.fullname}}

    def change_getter(self, cr, uid, ids, type_getter, context=None):
        if type_getter == 'partner':
            return {'domain': {'partner_id': [('customer', '=', True)]}}
        elif type_getter == 'partner_in':
            return {'domain': {'partner_id': [('supplier', '=', True)]}}
        else:
            return False

    def _set_number(self, cr, uid, account_id):
        number = str()
        account_pool = self.pool.get('account.account')
        account = account_pool.browse(cr, uid, account_id)
        if account_id:
            number = '%s%s' % (account.suffix, account.count)
            account_pool.write(cr, uid, account_id, {'count': account.count + account.step})
        return number

    def change_cash(self, cr, uid, ids, total, change, overrun, context=None):
        return {'value': {'cash_mr': self._calculate_cash(total, change, overrun)}}

    def _calculate_cash(self, total=0.0, change=0.0, overrun=0.0):
        return total - change + overrun

    def _get_cash(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = self._calculate_cash(record.total_mr, record.change_mr, record.overrun_mr)
        return res

    def _get_cash_dol(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = round(
                self._calculate_cash(record.total_mr, record.change_mr, record.overrun_mr) / record.rate, 2)
        return res

    def _search_cash(self, cr, uid, obj, name, args, context):
        ids = set()
        for cond in args:
            amount = cond[2]
            cr.execute(
                "select id from account_invoice where type='in_invoice' AND (COALESCE(total_mr, 0.00) - COALESCE(change_mr, 0.00) + COALESCE(overrun_mr, 0.00)) = %s",
                (amount,))
            res_ids = set(id[0] for id in cr.fetchall())

            ids = ids and (ids & res_ids) or res_ids
        if ids:
            return [('id', 'in', tuple(ids))]
        return [('id', '=', '0')]

    def _get_subtotal(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = sum([x.price_subtotal for x in record.invoice_line]) or 0.0
        return res

    def _get_lang(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = record.account_id.lang
        return res

    def _get_paid_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids):
            if record.state == 'paid' and record.pay_ids:
                res[record.id] = record.pay_ids[-1].date_pay
        return res

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        employee_pool = self.pool.get('hr.employee')
        for data in self.browse(cr, uid, ids, context):
            access = str()

            #  Автор + руководитель
            if data.user_id.id == uid or employee_pool.get_department_manager(cr, uid,
                                                                              employee_pool.get_employee(cr, uid,
                                                                                                         uid).id).user_id.id == uid:
                access += 'a'

            #  Директор UpSale
            if data.division_id and data.division_id.check_man_id.id == uid:
                access += 'p'

            #  Финансист
            users_f = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', [194, 17])], order='id')
            if uid in users_f:
                access += 'f'

            #  Руководители (чтоб менять автора)
            users_f = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', [152, 148])], order='id')
            if uid in users_f:
                access += 'r'

            val = False
            letter = name[6]
            if letter in access:
                val = True

            res[data.id] = val
        return res

    _columns = {
        'id': fields.integer(
            'ID',
            size=11,
            select=True,
            help='Порядковый номер'),
        'lead_id': fields.many2one(
            'crm.lead',
            'Кандидат',
            change_default=True,
            readonly=True,
            required=False,
            states={'draft': [('readonly', False)]},
            help=''
        ),
        'partner_id': fields.many2one(
            'res.partner',
            'Партнер',
            change_default=True,
            readonly=True,
            required=False,
            states={'draft': [('readonly', False)]},
            help='Партнер (сайт партнера)'
        ),

        'address_invoice_id': fields.many2one(
            'res.partner.address',
            'Invoice Address',
            readonly=True,
            required=False,
            states={'draft': [('readonly', False)]},
        ),
        'account_id': fields.many2one(
            'account.account',
            'Фирма',
            domain=[('type', '!=', 'closed'), ('company_id', '=', 4)],
            required=False,
            readonly=True,
            states={'draft': [('readonly', False)]},
            help='Фирма, от лица которой создается данный счет.'
        ),

        'bank_id': fields.many2one(
            'res.partner.bank',
            'Реквизиты',
            domain=[('name', '!=', False)],
            help='Банковские реквизиты Партнера'
        ),
        'pay_ids': fields.one2many('account.invoice.pay', 'invoice_id', 'Платежи', help='Платежи', ondelete='cascade'),
        'rate': fields.function(
            _get_rate,
            method=True,
            store=True,
            string='Курс',
            type='float',
            digits=(12, 4),
            readonly=True,
            help='Курс валют на дату выставления счета.'
        ),
        'tax': fields.related(
            'account_id',
            'tax',
            type='integer',
            string='Налог',
            readonly=True,
            help='Сумма налога по данному счету.'),
        'journal_id': fields.many2one(
            'account.journal',
            'Journal',
            required=False,
            readonly=True,
            states={'draft': [('readonly', False)]}
        ),
        'number': fields.char(
            'Номер',
            size=10,
            readonly=False,
            help='Номер счета.'),
        'notes': fields.text(
            'Комментарий',
            help='Комментарий.'),
        'type_account': fields.selection(
            [
                ('cash', 'Наличный'),
                ('cashless', 'Безналичный'),
                ('emoney', 'Електронные деньги')
            ],
            'Форма оплаты',
            help='Форма оплаты.'
        ),
        'untaxed': fields.function(
            _amount_all,
            digits_compute=dp.get_precision('Account'),
            string='Без налога',
            multi='all',
            store=False,
            readonly=True,
            help='Сумма счета без учета налога.'
        ),
        'a_tax': fields.function(
            _amount_all,
            digits_compute=dp.get_precision('Account'),
            string='Налог',
            multi='all',
            store=False,
            readonly=True,
            help='Сумма налога по данному счету.'
        ),
        'a_total': fields.function(
            _amount_all,
            digits_compute=dp.get_precision('Account'),
            string='Общая сумма',
            multi='all',
            store=False,
            readonly=True,
            help='Общая сумма счета.'
        ),
        'state': fields.selection(
            _states,
            'State',
            select=True,
            readonly=True,
            help=''),

        'check_p': fields.function(
            _check_access,
            method=True,
            string='Директор UpSale',
            type='boolean',
            invisible=True
        ),
        'check_a': fields.function(
            _check_access,
            method=True,
            string='Автор',
            type='boolean',
            invisible=True
        ),
        'check_f': fields.function(
            _check_access,
            method=True,
            string='Финансист',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Руководители (чтоб менять автора)',
            type='boolean',
            invisible=True
        ),
        'history_ids': fields.one2many(
            'account.invoice.history',
            'invoice_id',
            'История переходов',
            help='История переходов данного бланка.'),
        'invoice_line': fields.one2many(
            'account.invoice.line',
            'invoice_id',
            'Позиция счета',
            readonly=False,
            help='Список услуг и их стоимостей по данному счету.'
                 ' Таблица обязательная к заполнению на этапе создания счета'),

        'employee_id': fields.many2one(
            'hr.employee',
            'Сотрудник',
            states={'close': [('readonly', True)]},
            help='Сотрудник, для которого формируется данное ЗДС.'),
        'division_id': fields.many2one(
            'account.invoice.division',
            'Отдел',
            required=False,
            states={'close': [('readonly', True)]},
            help='Направление, для которого будут выданы денежные средства.'),
        'division': fields.boolean('Расходы общего назначения'),
        'get_division': fields.related('division_id', 'division', type='boolean'),
        'categ_id': fields.many2one(
            'account.invoice.category',
            'Статья расходов',
            required=False,
            domain="[('parent_id', '!=', False), ('division_id', '=', division_id)]",
            states={'close': [('readonly', True)]},
            help='Статья расходов, по которой необходимы денежные средства.'),
        'card_id': fields.many2one(
            'account.invoice.card',
            'Касса/банк/кошелек',
            required=False,
            help='В карточке ЗДС заполняется после выбора "Формы оплаты"'),
        'payment_details': fields.text(
            'Назначение платежа',
            required=False,
            states={'close': [('readonly', True)]},
            help='Текстовое поле, обязательное к заполнению на этапе создания ЗДС.'),
        'total_mr': fields.float(
            'Сумма',
            digits=(10, 2),
            required=False,
            states={'close': [('readonly', True)]},
            help='Сумма ЗДС.'),
        'change_mr': fields.float(
            'Сдача',
            digits=(10, 2),
            help='Заполняется финансистом при проведении ЗДС'),
        'overrun_mr': fields.float(
            'Перерасход',
            digits=(10, 2),
            help='Заполняется финансистом при проведении ЗДС'),
        'commission_mr': fields.float(
            'Комиссия',
            digits=(10, 2),
            help='Заполняется финансистом при проведении ЗДС'),
        'cash_mr': fields.function(
            _get_cash,
            method=True,
            string='Итого',
            type='float',
            digits_compute=dp.get_precision('Account'),
            fnct_search=_search_cash,
            help='Итоговая сумма ЗДС (без учета комиссии, сдачи и перерасхода)'
        ),
        'cash_mr_dol': fields.function(
            _get_cash_dol,
            method=True,
            string='Итого $',
            type='float',
            digits_compute=dp.get_precision('Account'),
            fnct_search=_search_cash,
            help='Итоговая сумма ЗДС $ (без учета комиссии, сдачи и перерасхода)'
        ),
        'companies_distribution': fields.selection(
            (
                ('100-0', '100/0'),
                ('0-100', '0/100'),
                ('50-50', '50/50'),
                ('85-15', '85/15'),
            ),
            'Распределение между компаниями (Up/INK)',
            required=False,
            states={'close': [('readonly', True)]},
            help='Процентное распределение суммы ЗДС между компаниями.'
        ),
        'type_getter': fields.selection(
            (
                ('lead', 'Кандидат'),
                ('partner', 'Партнер'),
                ('employee', 'Сотрудник'),
                ('partner_in', 'Поставщик'),
            ),
            'Тип получателя',
            required=False,
            states={'close': [('readonly', True)]},
            help='Выпадающий список. Обязательное к заполнению на этапе создания.\n'
                 'В зависимости от выбранного значения заполняются поля ниже: Сотрудник, Партнер, Поставщик'
        ),
        'attachment_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Вложения',
            domain=[('res_model', '=', 'account.invoice')],
            context={'res_model': 'account.invoice'},
            help='Прикрепленные файлы'
        ),

        'document_ids': fields.one2many(
            'account.invoice.documents',
            'invoice_id',
            'Закрывающие документы',
            ondelete='cascade',
            help='Список сформированных закрывающих документов по данному счету'),

        'lang': fields.function(
            _get_lang,
            method=True,
            string='Страна',
            type='char',
            help=''
        ),

        'a_subtotal': fields.function(
            _get_subtotal,
            method=True,
            string='Долг',
            type='float',
            digits_compute=dp.get_precision('Account'),
            help='Сумма долга по данному счету, просчитывается автоматически, в зависимости от внесенной оплаты',
        ),
        'date_mr': fields.date(
            'Дата проведения ЗДС',
            readonly=True,
            states={'proforma2': [('readonly', False)], 'close': [('readonly', False)]},
            help='Дата заполняется финансистом при проведении ЗДС'),
        'full_name': fields.related(
            'bank_id',
            'fullname',
            type='char',
            size=250,
            string='Полное наименование партнёра',
            store=False,
            help='Поле заполняется автоматически из реквизитов выбранного Партнера'
        ),

        'currency_id': fields.many2one(
            'res.currency',
            'Валюта',
            required=False,
            readonly=True,
            states={'draft': [('readonly', False)]},
            help='Заполняется автоматически, в зависимости от выбранной Фирмы'),
        'user_id': fields.many2one(
            'res.users',
            'Автор',
            readonly=False,
            help='Заполняется автоматически'),

        'state_document': fields.selection(
            (
                ('none', 'Не отгружены'),
                ('part', 'Частично отгружены'),
                ('full', 'Полностью отгружены'),
            ),
            'Статус ЗД',
        ),

        'paid_date': fields.function(
            _get_paid_date,
            type='date',
            string='Дата закрытия счета',
            store=True
        ),
        'plan_paid_date': fields.date('Планируемая дата оплаты'),
        'close_doc_create': fields.date('Дата отгрузки'),
        'check_man_id': fields.related(
            'division_id',
            'check_man_id',
            string='Ответственный',
            type='many2one',
            relation='res.users'
        ),
        'paid_type': fields.selection(
            (
                ('cash', 'Оплата'),
                ('pre', 'Предоплата'),
                ('sur', 'Доплата'),
                ('post', 'Пост оплата'),
            ), 'Тип счета'
        ),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'loyalty_ids': fields.one2many(
            'account.invoice.loyalty',
            'invoice_id',
            'Лояльность',
        ),
    }

    _defaults = {
        'date_invoice': fields.date.context_today,
        'check_a': True,
        'state_document': 'none',
    }

    def create(self, cr, uid, values, context=None):
        account_id = values.get('account_id', False)
        if account_id:
            currency_obj = self.pool.get('account.account').browse(cr, uid, account_id, context)
            values['number'] = self._set_number(cr, uid, account_id)
            values['currency_id'] = currency_obj.currency_id.id
        else:
            if values.get('card_id'):
                card = self.pool.get('account.invoice.card').browse(cr, uid, values['card_id'], context)
                values['currency_id'] = card.currency_id.id
            # записываю новые данные в услуги
        if values.get('invoice_line'):
            service_pool = self.pool.get('partner.added.services')
            for i in values.get('invoice_line'):
                if i[2].get('service_id') and values.get('partner_id') and values.get('date_invoice'):
                    i_ids = self.search(cr, 1, [
                        ('partner_id', '=', values['partner_id']),
                        ('date_invoice', '<', values['date_invoice']),
                        ('invoice_line.service_id', '=', i[2]['service_id'])
                    ])
                    if i_ids:
                        invoice = self.read(cr, 1, i_ids[0], ['date_invoice'])
                        date_start = invoice['date_invoice']
                    else:
                        date_start = values['date_invoice']

                    service_pool.connect_service(cr, values['partner_id'], i[2]['service_id'], date_start)
        return super(AccountInvoice, self).create(cr, uid, values, context)

    @notify.msg_send(_inherit)
    def write(self, cr, uid, ids, values, context=None):
        if values.get('amount_tax', False):
            del values['amount_tax']
        if values.get('amount_untaxed', False):
            del values['amount_untaxed']
        if values.get('amount_all', False):
            del values['amount_all']

        data = self.browse(cr, uid, ids)[0]

        next_state = values.get('state', False)
        state = data.state

        if next_state == 'close' and not values.get('date_mr', False) and not data.date_mr:
            values['date_mr'] = fields.date.context_today(self._inherit, cr, uid),

        if values.get('account_id', False):
            values['number'] = self._set_number(cr, uid, values['account_id'])

        if data.type == 'in_invoice':
            card_id = values.get('card_id', False) or data.card_id.id
            card = self.pool.get('account.invoice.card').browse(cr, uid, card_id, context)
            values['currency_id'] = card.currency_id.id

        if next_state and next_state != state:
            values.update({'history_ids': [(0, 0, {
                'state': self.get_state(next_state)[1]
            })]})

        if not sum([x.price_subtotal for x in data.invoice_line]):
            wf_service.trg_validate(uid, self._inherit, ids[0], 'invoice_paid', cr)
        elif sum([x.paid for x in data.invoice_line]):
            wf_service.trg_validate(uid, self._inherit, ids[0], 'invoice_proforma', cr)

        for attachment in values.get('attachment_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'account.invoice'

        if not data.partner_id and data.bank_id.partner_id:
            values['partner_id'] = data.bank_id.partner_id.id

        return super(AccountInvoice, self).write(cr, uid, ids, values, context)

    def unlink(self, cr, uid, ids, context=None):
        return super(Model, self).unlink(cr, uid, ids, context)


AccountInvoice()


class AccountInvoiceLine(Model):
    _inherit = 'account.invoice.line'

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        for record in self.browse(cr, uid, ids):
            val = self.onchange_price(
                cr,
                uid,
                ids,
                record.invoice_id.currency_id.id,
                record.invoice_id.date_invoice,
                record.paid,
                record.price_unit or 0.0,
                record.price_currency or 0.0

            )['value']
            res[record.id] = val['price_subtotal'] or 0.0
        return res

    def _show_number(self, cr, uid, ids, name, arg, context=None):
        data = self.browse(cr, uid, ids, context)
        result = {}
        i = 1
        for row in data:
            result[row.id] = i
            i += 1

        return result

    _columns = {
        'service_id': fields.many2one('brief.services.stage', 'Услуга', ondelete='set null',
                                      domain=[('in_account', '=', True)]),
        'name': fields.char('Description', size=256, required=False),
        'price_currency': fields.float('Стоимость в валюте счета', digits=(10, 6)),
        'price_subtotal': fields.function(
            _amount_line, string='Subtotal', type='float',
            digits=(10, 2), store=True),
        'paid': fields.float('Оплачено', digits=(10, 2)),
        'price_unit': fields.float('Unit Price', required=True, digits=(10, 6)),
        'account_id': fields.many2one('account.account', 'Account', required=True, domain=[]),
        'partner_id': fields.related('invoice_id', 'partner_id', string='Партнер', type='many2one',
                                     relation='res.partner', store=True),

        'nbr': fields.function(_show_number, method=True, string='Номер', type='integer', store=False),
        'brief_id': fields.many2one('brief.main', 'Медиаплан',
                                    domain="[('services_ids', '=', service_id), ('partner_id', '=', partner_id)]"),
        'no_brief': fields.boolean('Нет медиаплана'),
    }

    _defaults = {
        'account_id': lambda self, cr, uid, context: context.get('account_id', False),
        'name': lambda self, cr, uid, context: context.get('description', False),
        'partner_id': lambda self, cr, uid, context: context.get('partner_id', False),
    }

    def _check_unique_insesitive(self, cr, uid, ids, context=None):
        sr_ids = self.search(cr, 1, [('invoice_id.id', 'in', ids)], context)
        lst = [x.service_id.id for x in self.browse(cr, 1, sr_ids, context=context) if x.service_id]
        for self_obj in self.browse(cr, 1, ids, context=context):

            if self_obj.service_id and self_obj.service_id.id in lst:
                return False
            return True

    def _check_price(self, cr, uid, ids, context=None):
        for self_obj in self.browse(cr, 1, ids, context=context):
            if self_obj.price_unit <= 0.0:
                return False
            return True

    def onchange_price(self, cr, uid, ids, currency, date_invoice, paid, price_unit=0.0, price_currency=0.0,
                       context=None):
        currency_rate_pool = self.pool.get('res.currency.rate')
        currency_pool = self.pool.get('res.currency')
        currency_date_ids = currency_rate_pool.search(
            cr,
            uid,
            [
                ('name', '=', date_invoice),
                ('currency_id', '=', currency)
            ])

        if currency_date_ids:
            currency_date = currency_rate_pool.read(cr, uid, currency_date_ids[0], ['rate'])
        else:
            currency_date = currency_pool.read(cr, uid, currency, ['rate'])

        if price_unit:
            return {
                'value': {
                    'price_unit': price_unit,
                    'price_currency': price_unit * currency_date['rate'],
                    'price_subtotal': price_unit * currency_date['rate'] - paid
                }
            }
        if price_currency:
            return {
                'value': {
                    'price_unit': price_currency / currency_date['rate'],
                    'price_currency': price_currency,
                    'price_subtotal': price_currency - paid
                }
            }

    def create(self, cr, uid, values, context=None):
        invoice = self.pool.get('account.invoice').browse(cr, uid, values.get('invoice_id'))
        val = self.onchange_price(
            cr,
            uid,
            [i.id for i in invoice.invoice_line],
            invoice.currency_id.id,
            invoice.date_invoice,
            0,
            values.get('price_unit', 0.0),
            values.get('price_currency', 0.0),
        )['value']
        values.update(val)
        values['factor'] = values.get('price_unit', 0.0)
        if not values.get('no_brief') and not values.get('brief_id'):
            raise osv.except_osv('Позиция счета', 'Необходимо указать есть ли бриф или выбрать связанный бриф')
        return super(AccountInvoiceLine, self).create(cr, uid, values, context)

    def write(self, cr, uid, ids, values, context=None):
        if values.get('amount_tax', False):
            del values['amount_tax']
        if values.get('amount_untaxed', False):
            del values['amount_untaxed']
        if values.get('amount_all', False):
            del values['amount_all']
        if values.get('price_unit') or values.get('price_currency', False):
            for record in self.browse(cr, uid, ids):
                val = self.onchange_price(
                    cr,
                    uid,
                    ids,
                    record.invoice_id.currency_id.id,
                    record.invoice_id.date_invoice,
                    values.get('paid', False) or record.paid,
                    values.get('price_unit', False) or 0.0,
                    values.get('price_currency', False) or 0.0,
                )['value']
                if val:
                    values.update(val)
        flag = super(AccountInvoiceLine, self).write(cr, uid, ids, values, context)

        for record in self.browse(cr, uid, ids):

            document_sum = round(sum(x.document_cash for x in record.invoice_id.document_ids), 2)
            invoice_total = round(sum(x.price_currency for x in record.invoice_id.invoice_line), 2)

            if document_sum and invoice_total == document_sum:
                document_state = 'full'
            elif document_sum and invoice_total > document_sum:
                document_state = 'part'
            else:
                document_state = 'none'

            self.pool.get('account.invoice').write(cr, uid, [record.invoice_id.id], {'state_document': document_state})

            if record.invoice_id.state != 'draft':
                if not sum(x.price_subtotal for x in record.invoice_id.invoice_line):
                    wf_service.trg_validate(uid, 'account.invoice', record.invoice_id.id, 'invoice_paid', cr)
                elif sum(x.paid for x in record.invoice_id.invoice_line):
                    wf_service.trg_validate(uid, 'account.invoice', record.invoice_id.id, 'invoice_proforma', cr)
                else:
                    wf_service.trg_validate(uid, 'account.invoice', record.invoice_id.id, 'invoice_open', cr)

        return flag

    def unlink(self, cr, uid, ids, context=None):
        pay_line_pool = self.pool.get('account.invoice.pay.line')
        for record in self.browse(cr, uid, ids, context):
            if not pay_line_pool.search(cr, uid, [('invoice_id', '=', record.invoice_id.id),
                                                  ('service_id', '=', record.service_id.id)]):
                return super(AccountInvoiceLine, self).unlink(cr, uid, ids, context)
            else:
                raise osv.except_osv('Нельзя удалить!', 'Нельзя удалять позицию счета по которой уже проведена оплата!')

    _constraints = [
        #(_check_unique_insesitive, 'должна быть уникальной!', ['Услуга']),
        #(_check_unique_insesitive, 'Стоимость должна быть больше 0', []),
    ]


AccountInvoiceLine()


class AccountInvoicePay(Model):
    _name = 'account.invoice.pay'
    _description = u'AccountInvoice - Платежи'

    def _get_pay(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pay in self.browse(cr, uid, ids, context=context):
            res[pay.id] = {
                'total_pay': 0.0
            }

            res[pay.id]['total_pay'] = sum(line.name for line in pay.invoice_pay_ids)
        return res

    def change_card(self, cr, uid, ids, card_id, context=None):
        account_pool = self.pool.get('account.invoice.card')
        account_obj = account_pool.browse(cr, uid, card_id)
        return {'value': {'currency_id': account_obj.currency_id.id}}

    _columns = {
        'name': fields.integer('Номер платежа'),
        'date_pay': fields.date('Дата платежа'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice Reference', select=True),
        'invoice_pay_ids': fields.one2many('account.invoice.pay.line', 'invoice_pay_id', 'Платежи'),
        'currency_id': fields.many2one('res.currency', 'Валюта', required=True),
        'total_pay': fields.function(
            _get_pay,
            digits_compute=dp.get_precision('Account'),
            string='Сумма платежа',
            readonly=True,
            multi='all'
        ),
        'total': fields.float('Сумма платежа', digits=(10, 2)),
        'getter': fields.char('Входящее платежное поручение', size=250),
        'note': fields.text('Примечание', size=250),
        'type_account': fields.selection(
            [
                ('cash', 'Наличный'),
                ('cashless', 'Безналичный'),
                ('emoney', 'Електронные деньги')
            ], 'Форма оплаты'
        ),
        'card_id': fields.many2one('account.invoice.card', 'Касса/банк/кошелек', required=True),
        'partner_id': fields.related(
            'invoice_id',
            'partner_id',
            type="many2one",
            relation="res.partner",
            string="Партнер",
            store=False
        ),
        'lead_id': fields.related(
            'invoice_id',
            'lead_id',
            type="many2one",
            relation="crm.lead",
            string="Кандидат",
            store=False
        ),
    }

    def create(self, cr, user, vals, context=None):
        card_pool = self.pool.get('account.invoice.card')
        if vals.get('card_id', False):
            card = card_pool.browse(cr, user, vals['card_id'])
            vals['currency_id'] = card.currency_id.id
        return super(AccountInvoicePay, self).create(cr, user, vals, context)

    def unlink(self, cr, user, ids, context=None):
        line_pool = self.pool.get('account.invoice.pay.line')
        for record in self.read(cr, user, ids, ['invoice_pay_ids']):
            line_pool.unlink(cr, user, record['invoice_pay_ids'])
        return super(AccountInvoicePay, self).unlink(cr, user, ids, context)


AccountInvoicePay()


class AccountInvoicePayLine(Model):
    _name = 'account.invoice.pay.line'
    _description = u'AccountInvoice - Разбивка платежей'

    _columns = {
        'invoice_pay_id': fields.many2one(
            'account.invoice.pay',
            'Invoice Pay Reference',
            ondelete='cascade',
            select=True
        ),
        'invoice_id': fields.many2one('account.invoice', 'Invoice Reference', select=True),
        'service_id': fields.many2one('brief.services.stage', 'Услуга', ondelete='set null'),
        'name': fields.float('Сумма к оплате', digits_compute=dp.get_precision('Account')),
        'pay_date': fields.related('invoice_pay_id', 'date_pay', string='Дата платежа', type="date")
    }

    def get_invoice_amount(self, cr, uid, invoice_id, service_id):
        """
        Get invoice price in currency
        :param cr:
        :param uid:
        :param invoice_id:
        :param service_id:
        :return:
        """
        invoice_line_pool = self.pool.get('account.invoice.line')

        if isinstance(invoice_id, (list, tuple)):
            invoice_id = invoice_id[0]
        if isinstance(service_id, (list, tuple)):
            service_id = service_id[0]

        if invoice_id and service_id:
            line_ids = invoice_line_pool.search(
                cr,
                uid,
                [
                    ('invoice_id', '=', invoice_id),
                    ('service_id', '=', service_id)
                ])
            for line in invoice_line_pool.read(cr, uid, line_ids, ['price_currency']):
                return line['price_currency']
        return 0.0

    def get_invoice_pay(self, cr, uid, invoice_id, service_id):
        """
        Get invoice pay for service.
        :param cr:
        :param uid:
        :param invoice_id:
        :param service_id:
        :return:
        """
        pay_line_pool = self.pool.get('account.invoice.pay.line')

        if isinstance(invoice_id, (list, tuple)):
            invoice_id = invoice_id[0]
        if isinstance(service_id, (list, tuple)):
            service_id = service_id[0]

        if invoice_id and service_id:
            pay_line_ids = pay_line_pool.search(
                cr,
                uid,
                [
                    ('invoice_id', '=', invoice_id),
                    ('service_id', '=', service_id)
                ])
            pay = sum(item['name'] for item in pay_line_pool.read(cr, uid, pay_line_ids, ['name'])) or 0.0
            return pay
        return 0.0

    def update_line(self, cr, user, invoice_id, service_id):
        """
        Update Invoice line Paid and subtotal for service
        :param cr: Database Cursor
        :param user: User
        :param invoice_id:
        :param service_id:
        :return: True / False
        """
        invoice_line_pool = self.pool.get('account.invoice.line')

        if isinstance(invoice_id, (list, tuple)):
            invoice_id = invoice_id[0]
        if isinstance(service_id, (list, tuple)):
            service_id = service_id[0]

        amount = self.get_invoice_amount(cr, user, invoice_id, service_id)
        pay = self.get_invoice_pay(cr, user, invoice_id, service_id)

        line_ids = invoice_line_pool.search(
            cr,
            user,
            [
                ('invoice_id', '=', invoice_id),
                ('service_id', '=', service_id)
            ]
        )
        return invoice_line_pool.write(cr, user, line_ids, {'paid': pay, 'price_subtotal': amount - pay})

    def create(self, cr, user, vals, context=None):
        line_id = super(AccountInvoicePayLine, self).create(cr, user, vals, context)

        if vals.get('service_id', False) and vals.get('invoice_id', False):
            self.update_line(cr, user, vals['invoice_id'], vals['service_id'])
        return line_id

    def write(self, cr, user, ids, vals, context=None):
        flag = super(AccountInvoicePayLine, self).write(cr, user, ids, vals, context)
        for record in self.read(cr, user, ids, ['invoice_id', 'service_id']):
            self.update_line(cr, user, record['invoice_id'], record['service_id'])

        return flag

    def unlink(self, cr, user, ids, context=None):
        flag = True
        for record in self.read(cr, user, ids, ['invoice_id', 'service_id']):
            flag = super(AccountInvoicePayLine, self).unlink(cr, user, ids, context)
            self.update_line(cr, user, record['invoice_id'], record['service_id'])

        return flag


AccountInvoicePayLine()


class Account(Model):
    _inherit = 'account.account'

    _columns = {
        'tax': fields.integer('Налог'),
        'full': fields.char('Полное наименование фирмы', size=250),
        'inn': fields.char('ИНН / ІПН', size=10),
        'kpp': fields.char('КПП / № свідоцтва', size=9),
        'bik': fields.char('БИК / МФО', size=9),
        'bank': fields.char('Банк', size=250),
        'bank_number': fields.char('Сч. № банка', size=250),
        'account_number': fields.char('Сч. № получателя', size=250),
        'address': fields.char('Адрес', size=250),
        'phone': fields.char('Телефон', size=250),
        'responsible': fields.char('Ответственный за подписание', size=250),
        'lang': fields.selection(
            (
                ('ru', 'Россия'),
                ('ua', 'Украина'),
            ), 'Страна'
        ),

        'suffix': fields.char('Код фирмы', size=10),
        'count': fields.integer('Номер'),
        'step': fields.integer('Шаг'),
        'stamp': fields.binary('Печать'),
    }

    _defaults = {
        'tax': 0,
        'count': 2001,
        'step': 1
    }


Account()


class InvoiceHistory(Model):
    _name = 'account.invoice.history'
    _description = u'Invoice - История переходов'
    _log_create = True
    _order = 'create_date desc'
    _rec_name = 'state'

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел'),
        'state': fields.char('На этап', size=65),
        'create_date': fields.datetime('Дата', readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', invisible=True),
    }


InvoiceHistory()


class AccountInvoiceDivision(Model):
    _name = 'account.invoice.division'
    _description = u'Account - ЗДС - Отдел'

    _columns = {
        'name': fields.char('Отдел', size=250),
        'payment_man_id': fields.many2one('res.users', 'Кто проводит оплаты'),
        'check_man_id': fields.many2one('res.users', 'Кто утверждает оплаты'),
        'division': fields.boolean('Возможны ли расходы общего назначения?'),
    }


AccountInvoiceDivision()


class AccountInvoiceCategory(Model):
    _name = 'account.invoice.category'
    _description = u'Account - ЗДС - Назначение платежа'

    _columns = {
        'name': fields.char('Статья расходов', size=250),
        'parent_id': fields.many2one('account.invoice.category', 'Категория', select=True),
        'child_ids': fields.one2many('account.invoice.category', 'parent_id', 'Child Companies', invisible=True),
        'division_id': fields.many2one(
            'account.invoice.division',
            'Направление',
            help='Направление, для которого будут выданы денежные средства.'),
    }


AccountInvoiceCategory()


class AccountInvoiceCard(Model):
    _name = 'account.invoice.card'
    _description = u'Account - ЗДС - Касса'
    _order = "type_account, name"

    def _get_cash_in(self, cr, uid, ids, name, arg, context=None):
        pay_pool = self.pool.get('account.invoice.pay')
        transfer_pool = self.pool.get('account.invoice.transfer.funds')
        res = {}
        for record in self.browse(cr, uid, ids, context):
            pay_ids = pay_pool.search(cr, uid, [('card_id', '=', record.id)])
            pay_total = sum(x.total for x in pay_pool.browse(cr, uid, pay_ids))

            transfer_ids = transfer_pool.search(cr, uid, [('in_card_id', '=', record.id), ('state', '=', 'received')])
            transfer_total = sum(x.in_total for x in transfer_pool.browse(cr, uid, transfer_ids))

            res[record.id] = pay_total + transfer_total
        return res

    def _get_cash_out(self, cr, uid, ids, name, arg, context=None):
        invoice_pool = self.pool.get('account.invoice')
        transfer_pool = self.pool.get('account.invoice.transfer.funds')
        res = {}
        for record in self.browse(cr, uid, ids, context):
            pay_ids = invoice_pool.search(
                cr,
                uid,
                [
                    ('card_id', '=', record.id),
                    ('type', '=', 'in_invoice'),
                    ('state', '=', 'close')
                ]
            )
            pay_total = sum(x.cash_mr + x.commission_mr for x in invoice_pool.browse(cr, uid, pay_ids))

            transfer_ids = transfer_pool.search(
                cr,
                uid,
                [
                    ('out_card_id', '=', record.id),
                    ('state', '!=', 'draft')
                ])
            transfer_total = sum(x.out_total + x.commission for x in transfer_pool.browse(cr, uid, transfer_ids))

            res[record.id] = pay_total + transfer_total
        return res

    def _get_cash(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = record.cash_in - record.cash_out
        return res

    _columns = {
        'name': fields.char('Касса', size=250),
        'currency_id': fields.many2one('res.currency', 'Валюта', required=False),
        'type_account': fields.selection(
            [
                ('cashless', 'Безналичный'),
                ('cash', 'Наличный'),
                ('emoney', 'Електронные деньги')
            ], 'Форма оплаты'
        ),
        'cash_in': fields.function(
            _get_cash_in,
            method=True,
            string='Входящие средства',
            type='float',
            digits_compute=dp.get_precision('Account'),
        ),
        'cash_out': fields.function(
            _get_cash_out,
            method=True,
            string='Исходящие',
            type='float',
            digits_compute=dp.get_precision('Account'),
        ),
        'cash': fields.function(
            _get_cash,
            method=True,
            string='Итого',
            type='float',
            digits_compute=dp.get_precision('Account'),
        ),
        'sent_users_ids': fields.many2many(
            'res.users',
            'sent_fund_users_rel',
            'user_id',
            'card_id',
            'Кто может отправлять средства'),
        'get_users_ids': fields.many2many(
            'res.users',
            'get_fund_users_rel',
            'user_id',
            'card_id',
            'Кто может получать средства'),
    }


AccountInvoiceCard()


class AccountInvoiceDocuments(Model):
    _name = 'account.invoice.documents'
    _description = u'Account - Закрывающие документы'

    _columns = {
        'name': fields.selection(
            (
                ('completion_ru', 'Акт выполненных работ Россия'),
                ('completion_ua', 'Акт выполненных работ Украина'),
                ('facture_ru', 'Счет фактура Россия'),
                ('facture_ua', 'Счет фактура Украина')
            ), 'Тип документа'
        ),
        'document_date': fields.date('Дата в документе'),
        'document_cash': fields.float('Сумма в документе'),
        'document_line_id': fields.one2many('account.invoice.document.line', 'document_id', 'Справочник'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'lang': fields.related(
            'invoice_id',
            'lang',
            type="char",
            string="Страна",
            store=True
        ),
        'number': fields.related(
            'invoice_id',
            'number',
            type="char",
            size=10,
            string="Счет",
            store=True
        ),
        'partner_id': fields.related(
            'invoice_id',
            'partner_id',
            type="many2one",
            relation="res.partner",
            string="Партнер",
            store=True
        ),
        'user_id': fields.related(
            'invoice_id',
            'user_id',
            type="many2one",
            relation="res.users",
            string="Автор счета",
            store=True
        ),
        'a_total': fields.related(
            'invoice_id',
            'a_total',
            type="float",
            string="Сумма счета",
            store=True
        ),
        'date_invoice': fields.related(
            'invoice_id',
            'date_invoice',
            type="date",
            string="Дата выставления счета",
            store=True
        ),
        'document_state': fields.related(
            'invoice_id',
            'state_document',
            type="selection",
            selection=(
                ('none', 'Не отгружены'),
                ('part', 'Частично отгружены'),
                ('full', 'Полностью отгружены'),
            ),
            string="Статус ЗД",
            store=True
        ),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = dict()
        res = dict()
        if context.get('invoice', False):
            invoice = self.pool.get('account.invoice').browse(cr, uid, context['invoice'])

            service_list = list()
            for line in invoice.invoice_line:
                service_list.append({'service_id': line.service_id.id})

        return res

    def get_invoice_amount(self, cr, uid, invoice_id):
        if isinstance(invoice_id, (list, tuple)):
            invoice_id = invoice_id[0]

        invoice_pool = self.pool.get('account.invoice')
        if invoice_id:
            invoice = invoice_pool.browse(cr, uid, invoice_id)
            if invoice:
                return round(invoice.a_total, 2)
        return 0.0

    def get_document_pay(self, cr, uid, invoice_id):
        if isinstance(invoice_id, (list, tuple)):
            invoice_id = invoice_id[0]

        if invoice_id:
            document_ids = self.search(cr, uid, [('invoice_id', '=', invoice_id)])
            pay = sum(item['document_cash'] for item in self.read(cr, uid, document_ids, ['document_cash'])) or 0.0
            return round(pay, 2)
        return 0.0

    def get_invoice_state(self, cr, uid, invoice_id):
        if isinstance(invoice_id, (list, tuple)):
            invoice_id = invoice_id[0]

        invoice_ammount = self.get_invoice_amount(cr, uid, invoice_id)
        documents_pay = self.get_document_pay(cr, uid, invoice_id)
        if documents_pay and invoice_ammount == documents_pay:
            state = 'full'
        elif documents_pay and invoice_ammount > documents_pay:
            state = 'part'
        else:
            state = 'none'
        return state

    def create(self, cr, user, vals, context=None):
        document_id = super(AccountInvoiceDocuments, self).create(cr, user, vals, context)
        invoice_id = vals.get('invoice_id')
        if invoice_id:
            state = self.get_invoice_state(cr, user, invoice_id)
            self.pool.get('account.invoice').write(cr, user, [invoice_id], {'state_document': state})
        return document_id

    def write(self, cr, user, ids, vals, context=None):
        for record in self.read(cr, user, ids, ['invoice_id']):
            if record['invoice_id']:
                state = self.get_invoice_state(cr, user, record['invoice_id'])
                self.pool.get('account.invoice').write(cr, user, [record['invoice_id'][0]], {'state_document': state})
        return super(AccountInvoiceDocuments, self).write(cr, user, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        flag = True
        for record in self.read(cr, uid, ids, ['invoice_id']):
            flag = super(AccountInvoiceDocuments, self).unlink(cr, uid, ids)
            if isinstance(record['invoice_id'], (tuple, list)):
                invoice_id = record['invoice_id'][0]
            else:
                invoice_id = record['invoice_id']
            state = self.get_invoice_state(cr, uid, invoice_id)
            self.pool.get('account.invoice').write(cr, uid, [invoice_id], {'state_document': state})

        return flag


AccountInvoiceDocuments()


class AccountInvoiceDocumentLine(Model):
    _inherit = 'account.invoice.pay.line'
    _name = 'account.invoice.document.line'

    def _show_number(self, cr, uid, ids, name, arg, context=None):
        data = self.browse(cr, uid, ids, context)
        result = {}
        i = 1
        for row in data:
            result[row.id] = i
            i += 1

        return result

    _columns = {
        'document_id': fields.many2one('account.invoice.documents', 'Document'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга', ondelete='set null'),
        'name': fields.float('Сумма', digits=(10, 2)),
        'nbr': fields.function(_show_number, method=True, string='Номер', type='integer', store=False),
    }


AccountInvoiceDocumentLine()


class AccountInvoiceTransferFunds(Model):
    _name = 'account.invoice.transfer.funds'
    _description = u'Финансы - Перемещения'
    _rec_name = 'id'

    _states = (
        ('draft', 'Черновик'),
        ('sent', 'Деньги отправлены'),
        ('received', 'Деньги получены'),
    )

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for record in self.browse(cr, uid, ids, context):
            access = str()

            #  Может получить
            if record.in_card_id and uid in [x.id for x in record.in_card_id.get_users_ids]:
                access += 'g'

            #  Может отправить
            if record.out_card_id and uid in [x.id for x in record.out_card_id.sent_users_ids]:
                access += 's'

            val = False
            letter = name[6]
            if letter in access:
                val = True

            res[record.id] = val
        return res

    def change_card(self, cr, uid, ids, card_id, type_transfer='out', context=None):
        account_pool = self.pool.get('account.invoice.card')
        account_obj = account_pool.browse(cr, uid, card_id)
        flag = False
        if type_transfer == 'out':
            if uid in [x.id for x in account_obj.sent_users_ids]:
                flag = True
            value = {'out_currency_id': account_obj.currency_id.id, 'check_s': flag}
        else:
            if uid in [x.id for x in account_obj.get_users_ids]:
                flag = True
            value = {'in_currency_id': account_obj.currency_id.id, 'check_g': flag}
        return {'value': value}

    def change_rate(self, cr, uid, ids, in_currency, out_currency, out_total=0.0, rate=1, context=None):
        value = 0.0
        if in_currency and out_currency:
            if in_currency == out_currency:
                rate = 1
            value = out_total * rate
        return {'value': {'in_total': value, 'out_total': out_total}}
    _columns = {
        'id': fields.integer('Номер перемещения', size=11, select=True),
        'out_date': fields.date('Дата отправки денег', required=True),
        'out_type_account': fields.selection(
            [
                ('cash', 'Наличный'),
                ('cashless', 'Безналичный'),
                ('emoney', 'Електронные деньги')
            ], 'Форма отправленных денег', required=True
        ),
        'out_card_id': fields.many2one('account.invoice.card', 'Касса/банк/кошелек - отправитель', required=True),
        'out_total': fields.float('Сумма отправленная', digits=(10, 2), required=True),
        'out_currency_id': fields.many2one('res.currency', 'Валюта', required=True),

        'in_date': fields.date('Дата получения денег'),
        'in_type_account': fields.selection(
            [
                ('cash', 'Наличный'),
                ('cashless', 'Безналичный'),
                ('emoney', 'Електронные деньги')
            ], 'Форма полученных денег', required=True
        ),
        'in_card_id': fields.many2one('account.invoice.card', 'Касса/банк/кошелек - получатель', required=True),
        'in_total': fields.float('Сумма полученная', digits=(10, 2), required=True),
        'in_currency_id': fields.many2one('res.currency', 'Валюта', required=True),

        'commission': fields.float('Комиссия', digits=(10, 2)),
        'rate': fields.float('Курс', digits=(10, 4)),

        'comment': fields.text('Комментарий'),

        'state': fields.selection(_states, 'State', select=True, readonly=True),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Может отправить',
            type='boolean',
            invisible=True
        ),
        'check_g': fields.function(
            _check_access,
            method=True,
            string='Может получить',
            type='boolean',
            invisible=True
        ),
    }

    _defaults = {
        'state': 'draft',
        'out_date': fields.date.context_today,
        'rate': 1.0
    }

    def create(self, cr, uid, values, context=None):
        card_pool = self.pool.get('account.invoice.card')
        out_card_id = values.get('out_card_id', False)
        in_card_id = values.get('in_card_id', False)
        if out_card_id:
            currency_obj = card_pool.browse(cr, uid, out_card_id, context)
            values['out_currency_id'] = currency_obj.currency_id.id
        if in_card_id:
            currency_obj = card_pool.browse(cr, uid, in_card_id, context)
            values['in_currency_id'] = currency_obj.currency_id.id
        return super(AccountInvoiceTransferFunds, self).create(cr, uid, values, context)

    def write(self, cr, user, ids, vals, context=None):
        card_pool = self.pool.get('account.invoice.card')
        data = self.browse(cr, user, ids)[0]

        out_card_id = vals.get('out_card_id', False) or data.out_card_id.id
        in_card_id = vals.get('in_card_id', False) or data.in_card_id.id
        if out_card_id:
            currency_obj = card_pool.browse(cr, user, out_card_id, context)
            vals['out_currency_id'] = currency_obj.currency_id.id
        if in_card_id:
            currency_obj = card_pool.browse(cr, user, in_card_id, context)
            vals['in_currency_id'] = currency_obj.currency_id.id

        next_state = vals.get('state', False)
        state = data.state

        if next_state and next_state != state:
            if next_state == 'received' and not vals.get('in_date', False) and not data.in_date:
                raise osv.except_osv('Не заполнено поле', 'Необходимо заполнить Дату получения')

        return super(AccountInvoiceTransferFunds, self).write(cr, user, ids, vals, context)


AccountInvoiceTransferFunds()


class ResCurrencyRate(Model):
    _inherit = 'res.currency.rate'

    def _check_unique_insesitive(self, cr, uid, ids, context=None):
        for self_obj in self.browse(cr, 1, ids, context):
            if self.search(
                    cr,
                    1,
                    [
                        ('name', '=', self_obj.name),
                        ('currency_id.id', '=', self_obj.currency_id.id),
                        ('id', '!=', self_obj.id)
                    ], context):
                return False
            return True

    _constraints = [
        (
            _check_unique_insesitive,
            'Error: Нельзя ставить курс на одну и ту же дату дважды!',
            [u'Дата']
        )
    ]


ResCurrencyRate()


class AccountInvoiceLoyalty(Model):
    _name = 'account.invoice.loyalty'

    def get_services(self, cr, uid, ids, invoice_id, context=None):
        invoice_line_pool = self.pool.get('account.invoice.line')
        invoice_line_ids = invoice_line_pool.search(cr, 1, [('invoice_id', '=', invoice_id)])
        services = invoice_line_pool.read(cr, 1, invoice_line_ids, ['service_id'])
        res = [x['service_id'][0] for x in services]
        return {'domain': {'service_id': [('id', 'in', res)]}}

    def get_program(self, cr, uid, ids, service_id, invoice_id, context=None):
        programs = list()
        invoice_line_pool = self.pool.get('account.invoice.line')
        service_stage_pool = self.pool.get('brief.services.stage')
        process_lounch_pool = self.pool.get('process.launch')
        invoice_line_ids = invoice_line_pool.search(cr, 1, [('invoice_id', '=', invoice_id)])
        partner_id = invoice_line_pool.read(cr, 1, invoice_line_ids, ['partner_id'])
        need_invoice_ids = self.pool.get('account.invoice').search(cr, 1, [('partner_id', '=', partner_id[0]['partner_id'][0]), ('id', '<', invoice_id), ('type', '=', 'out_invoice')])
        need_invoice_line_ids = invoice_line_pool.search(cr, 1, [('invoice_id', 'in', need_invoice_ids)])
        services_ids = [serv['service_id'][0] for serv in invoice_line_pool.read(cr, 1, need_invoice_line_ids, ['service_id'])]

        #проверка что счет создается по услуге которую не покупал партнер ранее но уже покупал другие услуги
        if service_id not in services_ids and len(services_ids) >= 1:
            if len(need_invoice_ids) == 1:
                programs.append(1)
            elif len(need_invoice_ids) == 2:
                programs.append(2)
            elif len(need_invoice_ids) == 3:
                programs.append(3)
        brief_stage_data = service_stage_pool.read(cr, 1, service_id, ['usergroup'])

        #добавляю программы если партнер заказывает у нас какие-либо услуги, без привязки к бюджету
        if not brief_stage_data['usergroup']:
            programs.extend([4, 5, 6, 7, 8, 9, 10])

        #проверяю на входящие и исходящие и добавляю необходимые программы
        process_callin_ids = process_lounch_pool.search(cr, 1,  [
            ('partner_id', '=', partner_id[0]['partner_id'][0]),
            ('service_id', '=', service_id),
            ('process_model', '=', 'process.call.in')
        ])
        if process_callin_ids:
            programs.append(12)
        process_callout_ids = process_lounch_pool.search(cr, 1,  [
            ('partner_id', '=', partner_id[0]['partner_id'][0]),
            ('service_id', '=', service_id),
            ('process_model', '=', 'process.call.out')
        ])
        if process_callout_ids:
            programs.append(11)
        return {'domain': {'program_id': [('id', 'in', programs)]}}

    def get_bonus(self, cr, uid, ids, service_id, invoice_id, program_id, context=None):
        suma = self.pool.get('account.invoice').read(cr, 1, invoice_id, ['a_total'])
        suma = suma['a_total']
        if program_id == 1:
            proc = suma * 5 / 100
            suma -= proc
            return {'value': {'bonus_p': 5, 'bonus_sum': proc}}
        elif program_id == 2:
            proc = suma * 10 / 100
            suma -= proc
            return {'value': {'bonus_p': 10, 'bonus_sum': proc}}
        elif program_id == 3:
            proc = suma * 15 / 100
            suma -= proc
            return {'value': {'bonus_p': 15, 'bonus_sum': proc}}

    def get_calck(self, cr, uid, ids, program_id, invoice_id, bonus_p, bonus_sum):
        if program_id not in [1, 2, 3]:
            suma = self.pool.get('account.invoice').read(cr, 1, invoice_id, ['a_total'])
            suma = suma['a_total']
            if bonus_p:
                target = suma * bonus_p / 100
                return {'value': {'bonus_sum': target}}
            if bonus_sum:
                target = bonus_sum * 100 / suma
                return {'value': {'bonus_p': target}}

    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'номер счета'),
        'service_id': fields.many2one('brief.services.stage', 'Услуги'),
        'program_id': fields.many2one('account.invoice.programs', 'Программа'),
        'bonus_p': fields.float('% бонуса'),
        'bonus_sum': fields.float('Сумма бонуса'),
        'how_return': fields.selection(
            [
                ('beznal', 'Безнал'),
                ('e_cash', 'Электронный кошелек'),
                ('ad', 'В рекламу'),
                ('50_for_50', '50 на 50'),
                ('mks', 'Наличными в мск'),
                ('service', 'Услугой'),
            ], 'Как возвращать'
        ),
        'whom_return_partner': fields.many2one('res.partner', 'Кому возвращать (партнер)', inbisible=True),
        'whom_return_text': fields.char('Кому возвращать (текстовое)', size=128),
        'partner_id': fields.related(
            'invoice_id',
            'partner_id',
            type="many2one",
            relation="res.partner",
            string="Партнер",
            store=True
        ),
        'paid_date': fields.related(
            'invoice_id',
            'paid_date',
            type="date",
            string="Дата оплаты"
        )
    }

    _defaults = {
        'invoice_id': lambda s, c, u, context: context.get('invoice_id'),
    }

    def set_loyalty(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def loyalty_delete(self, cr, uid, ids, context):
        self.unlink(cr, uid, [context['loyalty']])

        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'account.invoice.form1'), ('model', '=', 'account.invoice')])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'name': 'Подключение услуги',
            'view_id': view_id,
            'res_id': context['invoice_id'] or 0,
            'type': 'ir.actions.act_window',
            'target': 'inline',
            'nodestroy': False,
            'context': {'add': True},
        }

    def create(self, cr, user, vals, context=None):
        bonus_data = self.get_bonus(cr, 1, 1, vals['service_id'], vals['invoice_id'], vals['program_id'], context)
        vals['bonus_p'] = bonus_data['value']['bonus_p']
        vals['bonus_sum'] = bonus_data['value']['bonus_sum']
        document_id = super(AccountInvoiceLoyalty, self).create(cr, user, vals, context)
        return document_id

AccountInvoiceLoyalty()


class AccountInvoicePrograms(Model):
    _name = 'account.invoice.programs'
    _columns = {
        'name': fields.char('Название программы', size=128)
    }
AccountInvoicePrograms()