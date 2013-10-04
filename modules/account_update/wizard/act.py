# -*- coding: utf-8 -*-
from datetime import date
from operator import itemgetter
from openerp.osv import fields
from openerp.osv.orm import TransientModel
from openerp.report import report_sxw
import time


class InvoiceActWizard(TransientModel):
    _name = 'account.invoice.act.wizard'
    _rec_name = 'account_id'

    _columns = {
        'account_id': fields.many2one('account.account', 'Фирма', domain=[('type', '!=', 'closed')],),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'bank_id': fields.many2one('res.partner.bank', 'Партнер', domain=[('partner_id', '!=', False), ('fullname', '!=', False), ('type', '!=', False)]),
        'date_start': fields.date('Начало периода'),
        'date_end': fields.date('Конец периода'),
        'prev_saldo': fields.float('Сальдо за предыдущий период', digits=(10, 2)),
        'saldo': fields.float('Сальдо', digits=(10, 2)),
        'credit': fields.float('Кредит', digits=(10, 2)),
        'debit': fields.float('Дебет', digits=(10, 2)),
        'act_ids': fields.one2many('account.invoice.act.line', 'act_id', 'Линии'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = dict()
        for field in self._columns.keys():
            if field in context:
                res[field] = context[field]
        return res

    def get_report(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        doc_pool = self.pool.get('account.invoice.documents')
        pay_pool = self.pool.get('account.invoice.pay')

        action_pool = self.pool.get('ir.actions.act_window')
        action_id = action_pool.search(cr, uid, [('name', '=', 'Акт сверки ')], context=context)

        for record in self.browse(cr, uid, ids, context):
            domain = [('account_id', '=', record.account_id.id)]
            if record.partner_id:
                domain += [('partner_id', '=', record.partner_id.id)]
            if record.bank_id:
                domain += [('bank_id', '=', record.bank_id.id)]

            invoice_ids = invoice_pool.search(cr, uid, domain)
            doc_prev_ids = doc_pool.search(cr, uid, [('invoice_id', 'in', invoice_ids), ('document_date', '<', record.date_start)])
            doc_prev_cash = sum([x.document_cash for x in doc_pool.browse(cr, uid, doc_prev_ids)]) or 0.0
            pay_prev_ids = pay_pool.search(cr, uid, [('invoice_id', 'in', invoice_ids), ('date_pay', '<', record.date_start)])
            pay_prev_cash = sum([x.total for x in pay_pool.browse(cr, uid, pay_prev_ids)]) or 0.0

            prev_saldo = pay_prev_cash - doc_prev_cash

            doc_ids = doc_pool.search(cr, uid, [('invoice_id', 'in', invoice_ids), ('document_date', '>=', record.date_start), ('document_date', '<=', record.date_end)])

            vals_list = list()

            pay_ids = pay_pool.search(cr, uid, [('invoice_id', 'in', invoice_ids), ('date_pay', '>=', record.date_start), ('date_pay', '<=', record.date_end)])

            pay_cash = 0.0
            for item in pay_pool.browse(cr, uid, pay_ids):
                vals = dict()

                vals['act_id'] = record.id
                vals['line_type'] = u'Платеж № {0} ({1})'.format(item.id, item.getter)
                vals['line_date'] = item.date_pay
                vals['line_cash'] = item.total
                vals['color_type'] = 'in'
                vals['pay_id'] = item.id

                vals_list.append(vals)
                pay_cash += item.total

            doc_cash = 0.0
            for item in doc_pool.browse(cr, uid, doc_ids):
                vals = dict()
                dd = u"{2}.{1}.{0}".format(*item.document_date.split('-'))

                vals['act_id'] = record.id
                vals['line_type'] = u'АВР ({0} от {1})'.format(item.id, dd)
                vals['line_date'] = item.document_date
                vals['line_cash'] = -item.document_cash
                vals['doc_id'] = item.id

                vals['color_type'] = 'out'

                vals_list.append(vals)
                doc_cash += item.document_cash

            saldo = pay_cash - doc_cash

            #line_ids = [(0, 0, item) for item in sorted(vals_list, key=itemgetter('line_date'))]
            line_ids = [(0, 0, item) for item in vals_list]

            if action_id:
                data = action_pool.read(cr, uid, action_id[0], context=context)

                data.update({
                    'nodestroy': True,
                    'context': {

                        'account_id': record.account_id.id,
                        #'partner_id': record.partner_id.id,
                        'bank_id': record.bank_id.id,
                        'date_start': record.date_start,
                        'date_end': record.date_end,
                        'prev_saldo': prev_saldo,
                        'saldo': saldo,
                        'credit': pay_cash,
                        'debit': doc_cash,
                        'act_ids': line_ids,
                    }
                })

                return data

InvoiceActWizard()


class InvoiceActLineWizard(TransientModel):
    _name = 'account.invoice.act.line'

    _columns = {
        'act_id': fields.many2one('account.invoice.act.wizard', 'Акт сверки'),
        'line_type': fields.char('Тип', size=200),
        'line_date': fields.date('Дата'),
        'line_cash': fields.float('Сумма', digits=(10, 2)),
        'color_type': fields.char('Тип для цвета', size=3),
        'doc_id': fields.many2one('account.invoice.documents', 'АВР'),
        'pay_id': fields.many2one('account.invoice.pay', 'Платеж'),
    }
InvoiceActLineWizard()


class InvoiceActReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self._cr = cr
        self._uid = 1
        super(InvoiceActReport, self).__init__(cr, 1, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_partner': self._get_partner_firm,
            'get_currency': self._get_currency,
        })

    def _get_partner_firm(self, bank):
        partner_full = bank.fullname
        partner_fio = bank.name or bank.passport
        partner = u""
        if partner_full:
            partner += partner_full
        if partner_fio:
            if partner:
                partner += u" / "
            partner += partner_fio
        return partner_full, partner_fio, partner

    def _get_currency(self, currency):
        return currency.symbol


report_sxw.report_sxw(
    'report.account.act.pdf',
    'account.invoice.act.wizard',
    'addons/account_update/wizard/act_pdf.mako',
    parser=InvoiceActReport
)