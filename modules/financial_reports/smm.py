# coding=utf-8
import calendar
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


class SMMReport(Model):
    _name = 'financial.reports.smm'
    _description = u'Финансовые отчеты - SMM'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for record_id in ids:
            access = str()

            #  Руководитель SMM (Григорьев)
            if uid == 544:
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
        domain = [
            ('service_id.direction', '=', 'SMM'),
            '|',
            ('close_date', '=', False),
            ('close_date', '>=', date_start),
            ('partner_id', '!=', False),
            ('invoice_id', '!=', False),
            #('specialist_id', '!=', False)
        ]
        pay_line_ids = pay_line_pool.search(cr, 1, domain, order='partner_id, service_id, invoice_date')
        lines = []
        # Итого
        total_period = 0
        balance_period = 0
        profit_period = 0
        costs_employee_period = 0
        costs_period = 0
        costs_partner_period = 0
        rollovers_income = 0
        rollovers_outcome = 0
        partners = set()

        costs_employee_period_tax = 0
        costs_employee_period_tax_ye = 0
        costs_tax_period = 0
        costs_tx_period_ye = 0
        employeers = set()

        for record in pay_line_pool.read(cr, 1, pay_line_ids, []):
            rate = 1
            costs_partner = record['add_costs']
            costs_employee = 0
            total = 0

            vals = {
                'service_id': record['service_id'][0] if record['service_id'] else False,
                'partner_id': record['partner_id'][0] if record['partner_id'] else False,
                'specialist_id': record['specialist_id'][0] if record['specialist_id'] else False,
                'paid_type': record['paid_type'] or 'cash',
                'invoice_id': record['invoice_id'][0] if record['invoice_id'] else False,
                'pay_date': record['invoice_date'],
                'total': record['factor'] + record['add_revenues'],
                'close_date': 'Не закрыт',

                'carry_over_revenue': 0,

                'co_costs_partner': 0,
                'costs_partner': 0,
                'co_costs_employee': 0,
                'costs_employee': 0,
                'profit': 0,
                'rate': 0,
            }
            if record['close'] and record['close_date'] <= date_end:
                vals['close_date'] = record['close_date']

            if record['invoice_id']:
                invoice = self.pool.get('account.invoice').read(cr, 1, record['invoice_id'][0], ['rate'])
                rate = invoice['rate']
                vals['rate'] = rate

            first_day = '{0}01'.format(record['invoice_date'][:-2],)
            source_date = datetime.strptime(record['invoice_date'], '%Y-%m-%d')
            day_in_month = calendar.monthrange(source_date.year, source_date.month)[1]
            last_day = '{0}{1}'.format(record['invoice_date'][:-2], day_in_month)

            if record['partner_id']:
                zds_ids = self.pool.get('account.invoice').search(
                    cr,
                    1,
                    [
                        ('division_id', '=', 2),
                        ('date_invoice', '<=', last_day),
                        ('type', '=', 'in_invoice'),
                        ('partner_id', '=', record['partner_id'][0])
                    ])
                for m in self.pool.get('account.invoice').read(cr, 1, zds_ids, ['cash_mr_dol', 'date_invoice']):
                    if m['date_invoice'] >= first_day:
                        vals['costs_partner'] += m['cash_mr_dol']
                    else:
                        vals['co_costs_partner'] += m['cash_mr_dol']

            if record['specialist_id']:
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
                    domain + [('specialist_id', '=', record['specialist_id'][0])],
                    order='partner_id, service_id, invoice_date'
                )
                sum_pay = sum(p['factor'] for p in pay_line_pool.read(cr, 1, specialist_pay_line_ids, ['factor']))
                try:
                    costs_employee = (total * record['factor'] / sum_pay) / 8.0
                except ZeroDivisionError:
                    costs_employee = 0

            if date_end >= record['invoice_date'] >= date_start and record['close_date'] != 'Не закрыт':
                vals['co_costs_employee'] = 0
                vals['costs_employee'] = costs_employee
                costs_employee_period += costs_employee

            else:
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
                raise osv.except_osv('PPC', 'Нельзя выбирать дату конца периода меньше чем дата начала периода')
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

        'line_ids': fields.function(
            _line_ids,
            relation='financial.reports.smm.line',
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
    }

    _defaults = {
        'state': 'draft',
        'check_h': lambda s, c, u, cnt: u == 544 or u == 1,
    }
SMMReport()


class SMMReportLine(Model):
    _name = 'financial.reports.smm.line'
    _description = u'Финансовые отчеты - SMM - Линия отчета'
    _order = 'partner_id, service_id, pay_date'

    _columns = {
        'report_id': fields.many2one('financial.reports.smm', 'Отчет SMM'),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'specialist_id': fields.many2one('res.users', 'Аккаунт-менеджер'),
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

        'carry_over_revenue': fields.float('Переходящие доходы, $'),

        'co_costs_partner': fields.float('Переходящие затраты на партнера, $'),
        'costs_partner': fields.float('Затраты на Партнера, $'),
        'co_costs_employee': fields.float('Переходящие затраты на персонал, $'),
        'costs_employee': fields.float('Затраты на персонал, $'),
        'profit': fields.float('Валовая прибыль, $'),
        'rate': fields.float('Курс'),
    }
SMMReportLine()