# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class accountBalanceWithClients(Model):
    _name = 'account.balance.client'
    _description = u'Баланс с партнером'
    _auto = False
    _rec_name = 'number'

    _columns = {
        'date_start': fields.date('с', select=True),
        'date_end': fields.date('по', select=True),

        'invoice_id': fields.many2one('account.invoice', 'Счет', readonly=True),
        'number': fields.char('Номер', size=10, readonly=True),

        'date_invoice': fields.date('Дата выставления счета', readonly=True),
        'pay_date': fields.date('Дата платежа', readonly=True),
        'document_date': fields.date('Дата АВР', readonly=True),

        'total': fields.float('Сумма счета', digits=(10, 2), readonly=True),
        'paid': fields.float('Оплаченная сумма', digits=(10, 2), readonly=True),
        'pay_total': fields.float('Сумма платежа', digits=(10, 2), readonly=True),
        'document_cash': fields.float('Сумма АВР', digits=(10, 2), readonly=True),
        'saldo': fields.float('Сальдо', digits=(10, 2), readonly=True),

        'lead_id': fields.many2one('crm.lead', 'Кандидат', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', readonly=True),
        'pay_id': fields.integer('Номер платежа', readonly=True),

    }

    _order = 'number'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        for indx, arg in enumerate(args):
            if arg[0] == 'date_start':
                args.append('|')
                args.append(['pay_date', '>=', arg[2]])
                args.append(['document_date', '>=', arg[2]])
            if arg[0] == 'date_end':
                args.append('|')
                args.append(['pay_date', '<=', arg[2]])
                args.append(['document_date', '<=', arg[2]])

        nargs = [arg for arg in args if arg[0] not in ('date_start', 'date_end')]
        return super(accountBalanceWithClients, self).search(cr, user, nargs, offset, limit, order, context, count)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for indx, arg in enumerate(domain):
            if arg[0] == 'date_start':
                domain.append('|')
                domain.append(['pay_date', '>=', arg[2]])
                domain.append(['document_date', '>=', arg[2]])
            if arg[0] == 'date_end':
                domain.append('|')
                domain.append(['pay_date', '<=', arg[2]])
                domain.append(['document_date', '<=', arg[2]])

        nargs = [arg for arg in domain if arg[0] not in ('date_start', 'date_end')]
        return super(accountBalanceWithClients, self).read_group(cr, uid, nargs, fields, groupby, offset, limit, context, orderby)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_balance_client')
        cr.execute('''
            CREATE OR REPLACE VIEW account_balance_client AS (
                SELECT
                    row_number() OVER () AS id,
                    x.*
                FROM (SELECT
                          to_char(NOW(), 'YYYY-MM-DD') date_end,
                          to_char(NOW(), 'YYYY-MM-DD') date_start,
                          i.id invoice_id,
                          i.date_invoice date_invoice,
                          i.number number,
                          i.partner_id partner_id,
                          i.lead_id lead_id,
                          sum(il.price_currency) total,
                          sum(il.paid) paid,
                          COALESCE(aid.document_cash, 0) document_cash,
                          to_char(aid.document_date, 'YYYY-MM-DD') document_date,
                          0 pay_id,
                          0.0 pay_total,
                          NULL pay_date,
                          0.0 - COALESCE(aid.document_cash, 0) saldo
                      FROM
                              account_invoice i
                              LEFT JOIN account_invoice_line il
                                  ON (il.invoice_id = i.id)
                              LEFT JOIN account_invoice_documents aid
                                  ON (aid.invoice_id = i.id AND aid.name IN ('completion_ru', 'completion_ua'))
                      WHERE
                          i.type = 'out_invoice' AND i.date_invoice IS NOT NULL AND aid.document_cash IS NOT NULL
                      GROUP BY
                          i.id,
                          i.number,
                          i.date_invoice,
                          i.partner_id,
                          i.lead_id,
                          aid.document_cash,
                          aid.document_date

                      UNION

                      SELECT
                          to_char(NOW(), 'YYYY-MM-DD') date_end,
                          to_char(NOW(), 'YYYY-MM-DD') date_start,
                          i.id invoice_id,
                          i.date_invoice date_invoice,
                          i.number number,
                          i.partner_id partner_id,
                          i.lead_id lead_id,
                          sum(il.price_currency) total,
                          sum(il.paid) paid,
                          0.0 document_cash,
                          NULL document_date,
                          aip.id pay_id,
                          aip.total pay_total,
                          to_char(aip.date_pay, 'YYYY-MM-DD') pay_date,
                          COALESCE(aip.total, 0) saldo
                      FROM
                              account_invoice i
                              LEFT JOIN account_invoice_line il
                                  ON (il.invoice_id = i.id)
                              LEFT JOIN account_invoice_pay aip
                                  ON (aip.invoice_id = i.id)
                      WHERE
                          i.type = 'out_invoice' AND i.date_invoice IS NOT NULL AND aip.id IS NOT NULL
                      GROUP BY
                          i.id,
                          i.number,
                          i.date_invoice,
                          i.partner_id,
                          i.lead_id,
                          aip.id,
                          aip.total,
                          aip.date_pay
                     ) x
            )
        ''')

accountBalanceWithClients()