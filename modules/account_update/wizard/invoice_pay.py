# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from datetime import datetime
from openerp.osv.orm import TransientModel


class InvoicePayWizard(TransientModel):
    _name = 'account.invoice.pay.wizard'

    def change_card(self, cr, uid, ids, card_id, context=None):
        account_pool = self.pool.get('account.invoice.card')
        account_obj = account_pool.browse(cr, uid, card_id)
        return {'value': {'currency_id': account_obj.currency_id.id}}

    _columns = {
        'invoice_id': fields.many2one('account.invoice', u'Счет'),
        'pay_linew_ids': fields.one2many(
            'account.invoice.pay.line.wizard',
            'wzr_id',
            u'Платеж'
        ),
        'getter': fields.char(u'Входящее платежное поручение', size=250),
        'type_account': fields.selection(
            [
                ('cash', u'Наличный'),
                ('cashless', u'Безналичный'),
                ('emoney', u'Електронные деньги')
            ], u'Форма оплаты'
        ),
        'card_id': fields.many2one('account.invoice.card', u'Касса/банк/кошелек', required=True),
        'currency_id': fields.many2one('res.currency', u'Валюта', required=False),
        'date_pay': fields.date('Дата платежа', required=False),
    }

    def default_get(self, cr, uid, fields, context=None):
        line_pool = self.pool.get('account.invoice.line')
        invoice_pool = self.pool.get('account.invoice')
        if context is None:
            context = {}
        res = dict()
        for field in self._columns.keys():
            if field in context:
                res[field] = context[field]

        if not res.get('invoice_id', False) and context.get('active_id', False):
            res['invoice_id'] = context['active_id']

        if not res.get('type_account') and res.get('invoice_id', False):
            invoice = invoice_pool.browse(cr, uid, res['invoice_id'])
            res['type_account'] = invoice.type_account

        plist = list()
        for p in line_pool.browse(cr, uid, line_pool.search(cr, uid, [('invoice_id', '=', res['invoice_id'])])):
            vals = dict()
            vals['service_id'] = p.service_id.id
            vals['name'] = p.price_currency - p.paid
            plist.append((0, 0, vals))
        res['pay_linew_ids'] = plist
        res['date_pay'] = datetime.today().strftime('%Y-%m-%d')
        return res

    def set_pay(self, cr, uid, ids, context=None):
        """
            @view_name - название view (своё для каждого партнера)
            @domain - фильтр записей конкретного партнера
            @res_id - список ids отсортиванный так, что бы первым был вновь созданный

            RETURN ir.actions.act_window

        """
        pay_line_pool = self.pool.get('account.invoice.pay.line')
        pay_pool = self.pool.get('account.invoice.pay')

        for record in self.browse(cr, uid, ids, context):
            if record.invoice_id and record.invoice_id.currency_id.id != record.currency_id.id:
                raise osv.except_osv('Warning!', 'Валюта платежа должна совпадать с валютой счета')

            pay_list = [(x.service_id.id, x.name) for x in record.pay_linew_ids if x.name]
            if pay_list:
                pay_ids = pay_pool.search(cr, uid, [('invoice_id', '=', record.invoice_id.id)])
                pay_id = pay_pool.create(
                    cr,
                    uid,
                    {
                        'name': len(pay_ids) + 1,
                        'date_pay': record.date_pay,
                        'invoice_id': record.invoice_id.id,
                        'total': sum([x[1] for x in pay_list]),
                        'card_id': record.card_id.id,
                        'type_account': record.type_account,
                        'currency_id': record.card_id.currency_id.id or 1,
                        'getter': record.getter,
                    }
                )
                self.pool.get('account.invoice').write(cr, uid, [record.invoice_id.id], {'type_account': record.type_account})
                for item in pay_list:
                    pay_line_pool.create(
                        cr,
                        uid,
                        {
                            'invoice_id': record.invoice_id.id,
                            'service_id': item[0],
                            'invoice_pay_id': pay_id,
                            'name': item[1]
                        }
                    )
        return {'type': 'ir.actions.act_window_close'}

InvoicePayWizard()


class AccountInvoicePayLineWizard(TransientModel):
    _name = "account.invoice.pay.line.wizard"
    _description = u"AccountInvoice - Платеж Wizard"

    _columns = {
        'service_id': fields.many2one('brief.services.stage', u'Услуга'),
        'name': fields.float(u'Сумма к оплате', digits=(10, 2)),
        'wzr_id': fields.many2one('account.invoice.pay.wizard', 'Wizard Pay'),
    }

AccountInvoicePayLineWizard()