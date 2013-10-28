# coding=utf-8
from datetime import datetime
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model


STATES = (
    ('draft', 'Отчет сгенерирован'),
    ('head', 'Утвержден руководителем'),
    ('director', 'Утвержден функциональным директором'),
    ('finansist', 'Утвержден финансистом'),
)


class ReportSeo(Model):
    _name = 'financial.reports.seo'
    _description = u'Финансовые отчеты - SEO'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for record_id in ids:
            access = str()

            #  Руководитель SEO (Паненко)
            if uid == 61:
                access += 'h'

            #  Функциональный директор (Чабанов Кирилл)
            if uid == 472:
                access += 'd'

            #  Финансист (Овчарова Таня)
            if uid == 170:
                access += 'f'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[record_id] = val
        return res

    def get_lines(self, cr, date_start, date_end):
        pay_line_pool = self.pool.get('account.invoice.pay.line')
        lines = []
        # Итого
        total_period = 0
        profit_period = 0
        costs_employee_period = 0
        costs_partner_period = 0
        rollovers_income = 0
        rollovers_outcome = 0
        partners = set()

        costs_employee_period_tax = 0
        costs_employee_period_tax_ye = 0
        costs_tax_period = 0
        costs_tx_period_ye = 0
        employeers = set()
        domain = [
            ('service_id.direction', '=', 'SEO'),
            '|',
            ('close_date', '=', False),
            ('close_date', '>=', date_start),
            ('partner_id', '!=', False),
            ('invoice_id', '!=', False),
            #('specialist_id', '!=', False)
        ]
        pay_line_ids = pay_line_pool.search(cr, 1, domain, context={'report': True})

        for record in pay_line_pool.read(cr, 1, pay_line_ids, []):
            costs_partner = 0
            costs_employee = 0
            total = 0

            vals = {
                'service_id': record['service_id'][0] if record['service_id'] else False,
                'partner_id': record['partner_id'][0] if record['partner_id'] else False,
                'specialist_id': record['specialist_id'][0] if record['specialist_id'] else False,
                'site_url': record['site_url'] or '',
                'paid_type': record['paid_type'] or 'cash',
                'invoice_id': record['invoice_id'][0] if record['invoice_id'] else False,
                'pay_date': record['invoice_date'],
                'total': record['factor'],
                'close_date': 'Не закрыт',
                'carry_over_revenue': 0,
                'co_costs_partner': 0,
                'costs_partner': 0,
                'co_costs_employee': 0,
                'costs_employee': 0,
                'profit': 0,
            }

            if record['close'] and record['close_date'] <= date_end:
                vals['close_date'] = record['close_date']

            source_date = datetime.strptime(record['invoice_date'], '%Y-%m-%d')
            period = self.pool.get('kpi.period').get_by_date(cr, source_date)
            if record['invoice_id'] and record['partner_id'] and record['service_id']:
                launch_ids = self.pool.get('process.launch').search(cr, 1, [('partner_id', '=', record['partner_id'][0]), ('service_id', '=', record['service_id'][0]), ('account_ids', 'in', [record['invoice_id'][0]])])
                if launch_ids:
                    launch = self.pool.get('process.launch').read(cr, 1, launch_ids[0], ['process_id', 'process_model'])
                    costs_ids = self.pool.get('process.costs').search(cr, 1, [('process_id', '=', launch['process_id']), ('process_model', '=', launch['process_model']), ('period_id', '=', period.id)])
                    costs_partner = sum(c['name'] for c in self.pool.get('process.costs').read(cr, 1, costs_ids, ['name']))

            if record['specialist_id']:
                source_date = datetime.strptime(record['invoice_date'], '%Y-%m-%d')
                period = self.pool.get('kpi.period').get_by_date(cr, source_date)
                kpi_ids = self.pool.get('kpi.kpi').search(cr, 1, [('period_id', '=', period.id), ('employee_id.user_id', '=', record['specialist_id'][0])])
                if kpi_ids:
                    kpi_total = self.pool.get('kpi.kpi')._get_cash(cr, 1, kpi_ids, 'total', None)
                    total = kpi_total[kpi_ids[0]]['total']

                    if record['specialist_id'][0] not in employeers:
                        employeers.add(record['specialist_id'][0])
                        kpi_elements = self.pool.get('kpi.kpi')._get_employee_items(cr, 1, kpi_ids, 'formal_tax', None)
                        tax = kpi_elements[kpi_ids[0]]
                        costs_employee_period_tax += total - tax
                        costs_employee_period_tax_ye += (total - tax) / 8.0
                        costs_tax_period += tax
                        costs_tx_period_ye += tax / 8.0

                specialist_pay_line_ids = pay_line_pool.search(
                    cr,
                    1,
                    domain + [('specialist_id', '=', record['specialist_id'][0])]
                )
                sum_pay = sum(p['factor'] for p in pay_line_pool.read(cr, 1, specialist_pay_line_ids, ['factor']))
                try:
                    costs_employee = (total * record['factor'] / sum_pay) / 8.0
                except ZeroDivisionError:
                    costs_employee = 0

            if date_end >= record['invoice_date'] >= date_start and record['close_date'] != 'Не закрыт':
                vals['co_costs_partner'] = 0
                vals['costs_partner'] = costs_partner
                vals['co_costs_employee'] = 0
                vals['costs_employee'] = costs_employee
                costs_employee_period += costs_employee
            else:
                vals['co_costs_partner'] = costs_partner
                vals['costs_partner'] = 0
                vals['co_costs_employee'] = costs_employee
                vals['costs_employee'] = 0
                vals['carry_over_revenue'] = record['factor']
                vals['total'] = 0

            if date_end >= record['invoice_date'] >= date_start:
                partners.add(record['partner_id'][0])
                total_period += vals['total']

            if date_end >= record['close_date'] >= date_start:
                costs_partner_period += vals['co_costs_partner'] + vals['costs_partner']
                vals['profit'] = vals['carry_over_revenue'] + vals['total'] - vals['co_costs_partner'] - vals['costs_partner'] - vals['co_costs_employee'] - vals['costs_employee']
                profit_period += vals['profit']
            elif vals['close_date'] == 'Не закрыт':
                rollovers_income += vals['carry_over_revenue'] + vals['total']
                rollovers_outcome += vals['co_costs_partner'] + vals['costs_partner']

            lines.append((0, 0, vals))

        costs_period = costs_employee_period + costs_partner_period
        balance_period = total_period - costs_period
        return lines, total_period, balance_period, profit_period, costs_employee_period, costs_period, costs_partner_period, rollovers_income, rollovers_outcome, len(partners), costs_employee_period_tax, costs_employee_period_tax_ye, costs_tax_period, costs_tx_period_ye

    def onchange_date(self, cr, uid, ids, date_start, date_end):
        if date_end and date_start:
            if date_end < date_start:
                raise osv.except_osv('SEO', 'Нельзя выбирать дату конца периода меньше чем дата начала периода')
            lines, total_period, balance_period, profit_period, costs_employee_period, costs_period, costs_partner_period, rollovers_income, rollovers_outcome, partners, costs_employee_period_tax, costs_employee_period_tax_ye, costs_tax_period, costs_tx_period_ye = self.get_lines(cr, date_start, date_end)
            return {'value': {
                'line_ids': lines,
                'total_period': total_period,
                'balance_period': balance_period,
                'profit_period': profit_period,
                'costs_employee_period': costs_employee_period,
                'costs_period': costs_period,
                'costs_partner_period': costs_partner_period,
                'rollovers_income': rollovers_income,
                'rollovers_outcome': rollovers_outcome,
                'count_partners': partners,
                'costs_employee_period_tax': costs_employee_period_tax,
                'costs_employee_period_tax_ye': costs_employee_period_tax_ye,
                'costs_tax_period': costs_tax_period,
                'costs_tx_period_ye': costs_tx_period_ye
            }}
        else:
            return {'value': {}}

    def _line_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for data in self.read(cr, uid, ids, ['start_date', 'end_date'], context):
            lines, total_period, balance_period, profit_period, costs_employee_period, costs_period, costs_partner_period, rollovers_income, rollovers_outcome, partners, costs_employee_period_tax, costs_employee_period_tax_ye, costs_tax_period, costs_tx_period_ye = self.get_lines(cr, data['start_date'], data['end_date'])
            res[data['id']] = {
                'line_ids': lines,
                'total_period': total_period,
                'balance_period': balance_period,
                'profit_period': profit_period,
                'costs_employee_period': costs_employee_period,
                'costs_period': costs_period,
                'costs_partner_period': costs_partner_period,
                'rollovers_income': rollovers_income,
                'rollovers_outcome': rollovers_outcome,
                'count_partners': partners,
                'costs_employee_period_tax': costs_employee_period_tax,
                'costs_employee_period_tax_ye': costs_employee_period_tax_ye,
                'costs_tax_period': costs_tax_period,
                'costs_tx_period_ye': costs_tx_period_ye
            }
        return res

    _columns = {
        'start_date': fields.date(
            'С',
            readonly=True,
            states={
                'draft': [('readonly', False)]
            }
        ),
        'end_date': fields.date(
            'По',
            readonly=True,
            states={
                'draft': [('readonly', False)]
            }
        ),
        'state': fields.selection(STATES, string='Статус', readonly=True,),
        'history_ids': fields.one2many(
            'financial.history',
            'financial_id',
            'История',
            readonly=True,
            domain=[('financial_model', '=', _name)],
            context={'financial_model': _name}),
        'check_h': fields.function(
            _check_access,
            method=True,
            string='Проверка на руководителя PPC',
            type='boolean',
            invisible=True
        ),
        'check_d': fields.function(
            _check_access,
            method=True,
            string='Проверка на функционального директора',
            type='boolean',
            invisible=True
        ),
        'check_f': fields.function(
            _check_access,
            method=True,
            string='Проверка на финансиста',
            type='boolean',
            invisible=True
        ),

        'line_ids': fields.function(
            _line_ids,
            relation='financial.reports.seo.line',
            type="one2many",
            string='Линии отчета',
            method=True,
            store=False,
            multi='report',
            readonly=True),
        'total_period': fields.function(
            _line_ids,
            type='float',
            string='Доход за период',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'balance_period': fields.function(
            _line_ids,
            type='float',
            string='Остаток денежного потока',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'profit_period': fields.function(
            _line_ids,
            type='float',
            string='Валовая прибыль',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'costs_employee_period': fields.function(
            _line_ids,
            type='float',
            string='Расходы на ЗП',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),
        'costs_period': fields.function(
            _line_ids,
            type='float',
            string='Расход за период',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'costs_partner_period': fields.function(
            _line_ids,
            type='float',
            string='Расходы на Партнера за период',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'rollovers_income': fields.function(
            _line_ids,
            type='float',
            string='Переходящие доходы',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'rollovers_outcome': fields.function(
            _line_ids,
            type='float',
            string='Переходящие расходы',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'count_partners': fields.function(
            _line_ids,
            type='integer',
            string='Всего партнеров шт.',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'costs_employee_period_tax': fields.function(
            _line_ids,
            type='integer',
            string='Зарплата',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'costs_employee_period_tax_ye': fields.function(
            _line_ids,
            type='integer',
            string='Зарплата, $',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'costs_tax_period': fields.function(
            _line_ids,
            type='integer',
            string='Налоги',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'costs_tx_period_ye': fields.function(
            _line_ids,
            type='integer',
            string='Налоги, $',
            method=True,
            store=False,
            multi='report',
            readonly=True
        ),

        'rate_rus': fields.float('Курс 1$ к руб.', readonly=True),
        'rate_uah': fields.float('Курс 1$ к грн.', readonly=True),
    }

    _defaults = {
        'state': 'draft',
        'check_h': lambda s, c, u, cnt: u == 61 or u == 1,
    }

    def get_rate(self, cr, date, currency_id):
        currency_rate_pool = self.pool.get('res.currency.rate')
        currency_pool = self.pool.get('res.currency')
        currency_date_ids = currency_rate_pool.search(
            cr,
            1,
            [('name', '=', date), ('currency_id', '=', currency_id)]
        )
        if currency_date_ids:
            currency = currency_rate_pool.read(cr, 1, currency_date_ids[0], ['rate'])
        else:
            currency = currency_pool.read(cr, 1, currency_id, ['rate'])
        return currency['rate']

    def create(self, cr, user, vals, context=None):
        date = datetime.now().strftime('%Y-%m-%d')
        vals['rate_rus'] = self.get_rate(cr, date, 31)
        vals['rate_uah'] = self.get_rate(cr, date, 23)

        return super(ReportSeo, self).create(cr, user, vals, context)

    def write(self, cr, user, ids, vals, context=None):
        date = datetime.now().strftime('%Y-%m-%d')
        for record in self.read(cr, user, ids, ['rate_rus', 'rate_uah']):
            if not record['rate_uah']:
                vals['rate_uah'] = self.get_rate(cr, date, 23)
            if not record['rate_rus']:
                vals['rate_rus'] = self.get_rate(cr, date, 31)
        return super(ReportSeo, self).write(cr, user, ids, vals, context)
ReportSeo()


class ReportSeoLine(Model):
    _name = 'financial.reports.seo.line'
    _description = u'Финансовые отчеты - SEO - Линия отчета'
    _order = 'partner_id ASC, service_id ASC, pay_date'

    _columns = {
        'report_id': fields.many2one('financial.reports.seo', 'Отчет SEO'),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'specialist_id': fields.many2one('res.users', 'Аккаунт-менеджер'),
        'site_url': fields.char('Сайт', size=250),
        'paid_type': fields.selection(
            (
                ('cash', 'Оплата'),
                ('pre', 'Предоплата'),
                ('sur', 'Доплата'),
                ('post', 'Пост оплата'),
            ), 'Тип оплаты'
        ),
        'invoice_id': fields.many2one('account.invoice', 'Счет'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'pay_date': fields.date('Дата платежа'),
        'total': fields.float('Сумма платежа $'),
        'close_date': fields.char('Дата ЗД', size=50),
        'carry_over_revenue': fields.float('Сумма поступления предыдущих периодов'),
        'co_costs_partner': fields.float('Переходящие затраты на партнера, $'),
        'costs_partner': fields.float('Затраты на Партнера, $'),
        'co_costs_employee': fields.float('Переходящие затраты на персонал, $'),
        'costs_employee': fields.float('Затраты на персонал, $'),
        'profit': fields.float('Валовая прибыль, $'),
    }

ReportSeoLine()