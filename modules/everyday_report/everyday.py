# coding=utf-8
import netsvc
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify


__author__ = 'andrey'


class DayReportPlan(Model):
    _name = 'day.report.plan'
    _description = u'Ежедневные отчеты - Планы'
    _rec_name = 'section_id'
    _order = 'date desc, section_id'

    _columns = {
        'uid': fields.many2one(
            'res.users',
            'Автор',
            readonly=True
        ),
        'section_id': fields.many2one(
            'crm.case.section',
            'Поднаправление',
            domain=[('id', 'child_of', [6])]
        ),
        'date': fields.date('Дата'),
        'plan': fields.float('План'),
    }

    _defaults = {
        'uid': lambda s, cr, u, ctxt: u,
        'section_id': lambda s, cr, u, ctxt: ctxt.get('context_section_id', False),
        'date': lambda *a: fields.date.today(),
    }

DayReportPlan()


class DayReportBriefPlan(Model):
    _name = 'day.report.brief.plan'
    _description = u'Ежедневные отчеты - Планы МП'
    _rec_name = 'direction'
    _order = 'date desc, direction'

    _columns = {
        'uid': fields.many2one(
            'res.users',
            'Автор',
            readonly=True
        ),
        'date': fields.date('Дата'),
        'plan': fields.integer('План'),
        'direction': fields.selection(
            (
                ('SITE', 'WEB'),
                ('CALL', 'КЦ'),
                ('SEO', 'SEO'),
                ('PPC', 'PPC'),
                ('SMM', 'SMM'),
                ('VIDEO', 'ViDEO'),
                ('MP', 'Медиапланирование'),
                ('MOSCOW', 'Москва'),
            ), 'Направление'
        )
    }

    _defaults = {
        'uid': lambda s, cr, u, ctxt: u,
        'date': lambda *a: fields.date.today(),
    }

DayReportBriefPlan()


class AccountInvoice(Model):
    _inherit = 'account.invoice'

    def _get_total_ye(self, cr, uid, ids, field_name, field_value, arg, context=None):
        result = {}
        for record in self.read(cr, uid, ids, ['invoice_line'], context=context):
            result[record['id']] = sum(r['price_unit'] for r in self.pool.get('account.invoice.line').read(cr, 1, record['invoice_line'], ['price_unit']))
        return result

    _columns = {
        'factor': fields.float('Коэффициент', digits=(10, 2)),
        'total_ye': fields.function(
            _get_total_ye,
            type="float",
            digits=(12, 2),
            string="Сумма счета в $",
            method=True,
            store=True
        )
    }

    _defaults = {
        'factor': 0,
    }
AccountInvoice()


class AccountInvoiceLine(Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'factor': fields.float('Новая сумма в $', digits=(10, 2)),
        'number': fields.related(
            'invoice_id',
            'number',
            string='Номер',
            type='char',
            size=100
        ),
        'user_id': fields.related(
            'invoice_id',
            'user_id',
            string='Автор',
            type='many2one',
            relation='res.users'
        ),

    }

    _defaults = {
        'factor': 0,
    }
AccountInvoiceLine()


class AccountInvoicePayLine(Model):
    _inherit = 'account.invoice.pay.line'

    def _get_total_ye(self, cr, uid, ids, field_name, field_value, arg, context=None):
        result = {}
        for record in self.read(cr, uid, ids, ['invoice_id', 'name'], context=context):
            result[record['id']] = 0
            if record['invoice_id']:
                invoice = self.pool.get('account.invoice').read(cr, 1, record['invoice_id'][0], ['rate'])
                total = record['name'] / invoice['rate']
                result[record['id']] = total
        return result

    _columns = {
        'factor': fields.float('Новая сумма в $', digits=(10, 2)),
        'number': fields.related(
            'invoice_id',
            'number',
            string='Номер',
            type='char',
            size=100
        ),
        'user_id': fields.related(
            'invoice_id',
            'user_id',
            string='Автор',
            type='many2one',
            relation='res.users'
        ),
        'name_ye': fields.function(
            _get_total_ye,
            type="float",
            digits=(12, 2),
            string="Сумма платежа в $",
            method=True,
            store=True,
            readonly=True
        ),
        'partner_id': fields.related(
            'invoice_id',
            'partner_id',
            string='Партнер',
            type='many2one',
            relation='res.partner',
            store=True
        ),
    }

    def create(self, cr, user, vals, context=None):
        if vals.get('name') and vals.get('invoice_id'):
            invoice = self.pool.get('account.invoice').read(cr, 1, vals['invoice_id'], ['rate'])
            if invoice:
                vals['factor'] = vals['name'] / invoice['rate']
        return super(AccountInvoicePayLine, self).create(cr, user, vals, context)
AccountInvoicePayLine()