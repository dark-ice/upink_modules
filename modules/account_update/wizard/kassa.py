# -*- coding: utf-8 -*-
from datetime import datetime
from operator import itemgetter
from openerp.osv import fields
from openerp.osv.orm import TransientModel


class InvoiceKassaWizard(TransientModel):
    _name = 'account.invoice.kassa.wizard'
    _rec_name = 'card_id'

    _columns = {
        'card_id': fields.many2one('account.invoice.card', 'Касса'),
        'date_start': fields.date('Начало периода'),
        'date_end': fields.date('Конец периода'),
        'saldo': fields.float('Остаток на последнюю дату выбранного периода', digits=(10, 2)),
        'total': fields.float('Остаток на текущий момент', digits=(10, 2)),
        'act_ids': fields.one2many('account.invoice.kassa.line', 'kassa_id', 'Линии'),
        'in_total': fields.float('Входящие средства за период', digits=(10, 2)),
        'out_total': fields.float('Исходящие средства за период', digits=(10, 2)),

    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = dict()
        for field in self._columns.keys():
            if field in context:
                res[field] = context[field]

        #res['date_start'] = datetime.today().strftime('%Y-%m-%d')
        #res['date_end'] = datetime.today().strftime('%Y-%m-%d')
        return res

    def get_report(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        transfer_pool = self.pool.get('account.invoice.transfer.funds')
        pay_pool = self.pool.get('account.invoice.pay')

        action_pool = self.pool.get('ir.actions.act_window')
        action_id = action_pool.search(cr, uid, [('name', '=', 'Касса ')], context=context)

        for record in self.browse(cr, uid, ids, context):

            transfer_out_ids = transfer_pool.search(cr, uid, [
                ('out_card_id', '=', record.card_id.id),
                ('out_date', '>=', record.date_start),
                ('out_date', '<=', record.date_end),
                ('state', '!=', 'draft')
            ])

            pay_ids = pay_pool.search(cr, uid, [
                ('card_id', '=', record.card_id.id),
                ('date_pay', '>=', record.date_start),
                ('date_pay', '<=', record.date_end)
            ])

            transfer_in_ids = transfer_pool.search(cr, uid, [
                ('in_card_id', '=', record.card_id.id),
                ('in_date', '>=', record.date_start),
                ('in_date', '<=', record.date_end),
                ('state', '=', 'received')
            ])

            out_ids = invoice_pool.search(cr, uid, [
                ('card_id', '=', record.card_id.id),
                ('type', '=', 'in_invoice'),
                ('date_mr', '>=', record.date_start),
                ('date_mr', '<=', record.date_end),
                ('state', '=', 'close')
            ])

            p_transfer_out_ids = transfer_pool.search(cr, uid, [
                ('out_card_id', '=', record.card_id.id),
                ('out_date', '<=', record.date_end),
                ('state', '!=', 'draft')
            ])

            p_pay_ids = pay_pool.search(cr, uid, [
                ('card_id', '=', record.card_id.id),
                ('date_pay', '<=', record.date_end)
            ])

            p_transfer_in_ids = transfer_pool.search(cr, uid, [
                ('in_card_id', '=', record.card_id.id),
                ('in_date', '<=', record.date_end),
                ('state', '=', 'received')
            ])

            p_out_ids = invoice_pool.search(cr, uid, [
                ('card_id', '=', record.card_id.id),
                ('type', '=', 'in_invoice'),
                ('date_mr', '<=', record.date_end),
                ('state', '=', 'close')
            ])

            out_t = sum(-1 * (item.out_total + item.commission) for item in transfer_pool.browse(cr, uid, p_transfer_out_ids))
            in_t = sum(item.in_total for item in transfer_pool.browse(cr, uid, p_transfer_in_ids))
            p_t = sum(item.total for item in pay_pool.browse(cr, uid, p_pay_ids))
            i_t = sum(-1 * (item.cash_mr + item.commission_mr) for item in invoice_pool.browse(cr, uid, p_out_ids))

            vals_list = list()
            in_total = 0.0
            out_total = 0.0
            for item in transfer_pool.browse(cr, uid, transfer_out_ids):
                vals = {
                    'kassa_id': record.id,
                    'line_type': u'Перемещение из № {0}.'.format(item.id),
                    'color_type': 'out',
                    'line_date': item.out_date,
                    'line_out': -item.out_total,
                    'transfer_id': item.id
                }
                out_total += item.out_total + item.commission
                vals_list.append(vals)
                if item.commission != 0:
                    vals = {
                        'kassa_id': record.id,
                        'line_type': u'Комиссия на перемещение из № {0}.'.format(item.id),
                        'color_type': 'out',
                        'line_date': item.out_date,
                        'line_out': -item.commission,
                        'transfer_id': item.id
                    }
                    vals_list.append(vals)

            for item in transfer_pool.browse(cr, uid, transfer_in_ids):
                vals = {
                    'kassa_id': record.id,
                    'line_type': u'Перемещение в № {0}.'.format(item.id),
                    'color_type': 'in',
                    'line_date': item.in_date,
                    'line_in': item.in_total,
                    'transfer_id': item.id
                }
                in_total += item.in_total
                vals_list.append(vals)

            for item in pay_pool.browse(cr, uid, pay_ids):
                line = u'Платеж № {0}.'.format(item.id)
                if item.invoice_id:
                    line += u' Номер счета: {0}'.format(item.invoice_id.number)
                vals = {
                    'kassa_id': record.id,
                    'line_type': line,
                    'color_type': 'in',
                    'line_date': item.date_pay,
                    'line_in': item.total,
                    'pay_id': item.id
                }

                in_total += item.total
                vals_list.append(vals)

            for item in invoice_pool.browse(cr, uid, out_ids):
                vals = {
                    'kassa_id': record.id,
                    'line_type': u'ЗДС № {0}. Назначение платежа: {1}. Автор: {2}'.format(item.id, item.payment_details, item.user_id.name),
                    'color_type': 'out',
                    'line_date': item.date_mr,
                    'line_out': -item.cash_mr,
                    'invoice_id': item.id
                }

                out_total += item.cash_mr + item.commission_mr
                vals_list.append(vals)

                if item.commission_mr != 0:
                    vals = {
                        'kassa_id': record.id,
                        'line_type': u'Комиссия на ЗДС № {0}.'.format(item.id),
                        'color_type': 'out',
                        'line_date': item.date_mr,
                        'line_out': -item.commission_mr,
                        'invoice_id': item.id
                    }

                    vals_list.append(vals)

            line_ids = [(0, 0, item) for item in sorted(vals_list, key=itemgetter('line_date'))]

            saldo = in_t + out_t + p_t + i_t

            if action_id:
                data = action_pool.read(cr, uid, action_id[0], context=context)

                data.update({
                    'nodestroy': True,
                    'context': {
                        'card_id': record.card_id.id,
                        'date_start': record.date_start,
                        'date_end': record.date_end,
                        'saldo': saldo,
                        'total': record.card_id.cash,
                        'act_ids': line_ids,
                        'in_total': in_total,
                        'out_total': out_total,
                    }
                })

                return data

InvoiceKassaWizard()


class InvoiceKassaLineWizard(TransientModel):
    _name = 'account.invoice.kassa.line'
    _order = 'line_date'
    _rec_name = 'line_type'

    _columns = {
        'kassa_id': fields.many2one('account.invoice.kassa.wizard', 'Касса'),
        'line_type': fields.char('Тип', size=250),
        'color_type': fields.char('Тип для цвета', size=3),
        'line_date': fields.date('Дата'),
        'line_cash': fields.float('Сумма', digits=(10, 2)),
        'line_in': fields.float('Приход', digits=(10, 2)),
        'line_out': fields.float('Расход', digits=(10, 2)),
        'transfer_id': fields.many2one('account.invoice.transfer.funds', 'Перемещение'),
        'invoice_id': fields.many2one('account.invoice', 'ЗДС', domain=[('type', '=', 'in_invoice')]),
        'pay_id': fields.many2one('account.invoice.pay', 'Платеж'),
    }
InvoiceKassaLineWizard()