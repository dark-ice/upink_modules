# coding=utf-8
import calendar
from datetime import date, datetime
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


STATES = (
    ('draft', 'Отчет сгенерирован'),
    ('head', 'Утвержден руководителем'),
    ('director', 'Утвержден функциональным директором'),
    ('finansist', 'Утвержден финансистом'),
)


class PPCReport(Model):
    _name = 'financial.reports.ppc'
    _description = u'Финансовые отчеты - PPC'

    def get_lines(self, cr, date_start, date_end):
        pay_line_pool = self.pool.get('account.invoice.pay.line')
        domain = [
            ('service_id.direction', '=', 'PPC'),
            '|',
            ('close_date', '=', False),
            ('close_date', '>=', date_start),
        ]
        pay_line_ids = pay_line_pool.search(cr, 1, domain)
        lines = []
        for record in pay_line_pool.read(cr, 1, pay_line_ids, []):
            google = False
            rate = 1
            vals = {
                'service_id': record['service_id'][0] if record['service_id'] else False,
                'partner_id': record['partner_id'][0] if record['partner_id'] else False,
                'specialist_id': record['specialist_id'][0] if record['specialist_id'] else False,
                'paid_type': record['paid_type'] or 'cash',
                'invoice_id': record['invoice_id'][0] if record['invoice_id'] else False,
                'pay_date': record['invoice_date'],
                'total': record['factor'],
                'close_date': 'Не закрыт',

                'carry_over_revenue': 0,

                'discount_up': 0,
                'discount_partner': 0,
                'discount_nds': 0,

                'co_costs_partner': 0,
                'costs_partner': 0,
                'co_costs_employee': 0,
                'costs_employee': 0,
                'profit': 0,
            }
            if record['close_date'] < date_end:
                vals['close_date'] = record['close_date']

            if record['partner_id']:
                discounts_ids = self.pool.get('res.partner.ppc.discounts').search(
                    cr,
                    1,
                    [
                        ('service_id', '=', record['service_id'][0]),
                        ('partner_id', '=', record['partner_id'][0]),
                        '|',
                        '&', ('start_date', '<=', record['invoice_date']), ('finish_date', '>=', record['invoice_date']),
                        ('permanent', '=', True),
                    ]
                )
                for discount in self.pool.get('res.partner.ppc.discounts').read(cr, 1, discounts_ids, []):
                    if discount['discount_type'] == 'nds':
                        vals['discount_nds'] = discount['percent']
                    elif discount['discount_type'] == 'partner_discount':
                        vals['discount_partner'] = discount['percent']
                    elif discount['discount_type'] == 'yandex_discount':
                        vals['discount_up'] = discount['percent']
                    elif discount['discount_type'] == 'google_discount':
                        if discount['google']:
                            vals['discount_up'] = 4500
                            google = True
                        else:
                            vals['discount_up'] = discount['percent']

            if vals['discount_nds'] == 0:
                vals['discount_nds'] = 1.18
            if record['invoice_id']:
                invoice = self.pool.get('account.invoice').read(cr, 1, record['invoice_id'][0], ['rate'])
                rate = invoice['rate']

            if record['service_id'][0] in (17, 21, 22, ):
                # 30 - курс долара у Яндекса
                vals['costs_partner'] = (1 - vals['discount_up'] / 100) * record['factor'] * rate / 30
            elif record['service_id'][0] in (18, ):
                if google:
                    vals['costs_partner'] = (record['factor'] - 4500 / rate) / vals['discount_nds']
                else:
                    vals['costs_partner'] = record['factor'] * (1 - vals['discount_up'] / 100) / vals['discount_nds']

            if vals['close_date'] == 'Не закрыт':
                vals['carry_over_revenue'] = record['factor']
            else:
                pass

            lines.append((0, 0, vals))

        return lines

    def onchange_date(self, cr, uid, ids, date_start, date_end):
        if date_end and date_start:
            lines = self.get_lines(cr, date_start, date_end)
            return {'value': {'line_ids': lines}}
        else:
            return {'value': {}}

    def _line_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for data in self.read(cr, uid, ids, ['start_date', 'end_date'], context):
            lines = self.get_lines(cr, data['start_date'], data['end_date'])
            res[data['id']] = 0
        return res

    _columns = {
        'start_date': fields.date('С'),
        'end_date': fields.date('По'),
        'state': fields.selection(STATES, string='Статус'),

        'history_ids': fields.one2many(
            'financial.history',
            'financial_id',
            'История',
            domain=[('financial_model', '=', _name)],
            context={'financial_model': _name}),

        'line_ids': fields.function(
            _line_ids,
            relation='financial.reports.ppc.line',
            type="one2many",
            string='Линии отчета',
            method=True,
            store=False,
            readonly=True),
    }
PPCReport()


class PPCReportLine(Model):
    _name = 'financial.reports.ppc.line'
    _description = u'Финансовые отчеты - PPC - Линия отчета'
    _order = 'partner_id, service_id, pay_date'

    _columns = {
        'report_id': fields.many2one('financial.reports.ppc', 'Отчет PPC'),
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

        'carry_over_revenue': fields.float('Переходящие доходы'),

        'discount_up': fields.float('Скидка Up в аккаунте'),
        'discount_partner': fields.float('Скидка Партнера'),
        'discount_nds': fields.float('НДС'),

        'co_costs_partner': fields.float('Переходящие затраты на партнера'),
        'costs_partner': fields.float('Затраты на Партнера'),
        'co_costs_employee': fields.float('Переходящие затраты на персонал'),
        'costs_employee': fields.float('Затраты на персонал'),
        'profit': fields.float('Валовая прибыль'),
    }
PPCReportLine()