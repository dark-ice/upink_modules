# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class accountActReport(Model):
    _name = 'account.act.report'
    _description = u'Акт сверки'
    _auto = False
    _rec_name = 'account_id'

    _columns = {
        'date_start': fields.date('с', select=True),
        'date_end': fields.date('по', select=True),

        'pay_date': fields.date('Дата платежа', readonly=True),
        'document_date': fields.date('Дата АВР', readonly=True),

        'pay_total': fields.float('Сумма платежа', digits=(10, 2), readonly=True),
        'document_cash': fields.float('Сумма АВР', digits=(10, 2), readonly=True),
        'saldo': fields.float('Сальдо', digits=(10, 2), readonly=True),

        'account_id': fields.many2one('account.account', 'Фирма', readonly=True),
        'lead_id': fields.many2one('crm.lead', 'Кандидат', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', readonly=True),

    }

    _order = 'account_id'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        account_id = [item for item in args if item[0] == 'account_id']
        lead_id = [item for item in args if item[0] == 'lead_id']
        partner_id = [item for item in args if item[0] == 'partner_id']
        date_start = [item for item in args if item[0] == 'date_start']
        date_end = [item for item in args if item[0] == 'date_end']
        if date_start:
            context['date_start'] = date_start[0][2]
        if date_end:
            context['date_end'] = date_end[0][2]
        if account_id:
            context['account_id'] = account_id[0][2]
        if lead_id:
            context['lead_id'] = lead_id[0][2]
        if partner_id:
            context['partner_id'] = partner_id[0][2]

        return super(accountActReport, self).search(cr, user, [], offset, limit, order, context, count)

    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        date_start = context.get("date_start", False)
        date_end = context.get("date_end", False)
        account_id = context.get("account_id", False)
        lead_id = context.get("lead_id", False)
        partner_id = context.get("partner_id", False)
        #return self.get_records(cr, date_start, date_end, account_id, lead_id, partner_id)
        return super(accountActReport, self).read(cr, user, ids, fields, context, load)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        date_start = [item for item in domain if item[0] == 'date_start']
        date_end = [item for item in domain if item[0] == 'date_end']

        new_domain = []

        if date_start:
            date_s = [('pay_date', '>=', date_start[0][2]), ('document_date', '>=', date_start[0][2])]
            new_domain += date_s

        if date_end:
            date_e = [('pay_date', '<=', date_end[0][2]), ('document_date', '<=', date_end[0][2])]
            new_domain += date_e
        new_domain = ['|'] * (len(new_domain) - 1) + new_domain
        return super(accountActReport, self).read_group(cr, uid, new_domain, fields, groupby, offset, limit, context, orderby)

    def get_records(self, cr, date_start, date_end, account_id, lead_id, partner_id):
        query_x = str()
        query_z = str()

        if date_start:
            query_x += " AND aid.document_date >='%s'::timestamp" % date_start
            query_z += " AND aip.date_pay >='%s'::timestamp" % date_start
        if date_end:
            query_x += " AND aid.document_date <='%s'::timestamp" % date_end
            query_z += " AND aip.date_pay <='%s'::timestamp" % date_end
        if account_id:
            query_x += ' AND a.id =%s' % account_id
            query_z += ' AND a.id =%s' % account_id
        if lead_id:
            query_x += ' AND a.lead_id =%s' % lead_id
            query_z += ' AND a.lead_id =%s' % lead_id
        if partner_id:
            query_x += ' AND a.partner_id =%s' % partner_id
            query_z += ' AND a.partner_id =%s' % partner_id

        cr.execute("SELECT\
                    row_number() over() as id,\
                    to_char(NOW(), 'YYYY-MM-DD') date_end,\
                    to_char(NOW(), 'YYYY-MM-DD') date_start,\
                    x.*\
                FROM (SELECT\
                            a.id account_id,\
                            i.partner_id partner_id,\
                            i.lead_id lead_id,\
                            aid.document_date document_date,\
                            aid.document_cash document_cash,\
                            NULL pay_date,\
                            0.0 pay_total,\
                            0.0 - COALESCE(aid.document_cash, 0) saldo\
                        FROM\
                            account_account a\
                            LEFT JOIN account_invoice i\
                                ON (i.account_id = a.id)\
                            LEFT JOIN account_invoice_documents aid\
                                ON (aid.invoice_id = i.id AND aid.name in ('completion_ru', 'completion_ua') AND aid.document_cash > 0)\
                        WHERE\
                            i.type='out_invoice' AND aid.document_cash > 0 " + query_x + "\
                        GROUP BY\
                            a.id,\
                            i.partner_id,\
                            i.lead_id,\
                            aid.document_date,\
                            aid.document_cash\
                        UNION\
                        SELECT\
                            a.id account_id,\
                            i.partner_id partner_id,\
                            i.lead_id lead_id,\
                            NULL document_date,\
                            0.0 document_cash,\
                            aip.date_pay pay_date,\
                            aip.total pay_total,\
                            COALESCE(aip.total, 0) saldo\
                        FROM\
                            account_account a\
                            LEFT JOIN account_invoice i\
                                ON (i.account_id = a.id)\
                            LEFT JOIN account_invoice_pay aip\
                                ON (aip.invoice_id = i.id AND aip.total > 0)\
                        WHERE\
                            i.type='out_invoice' AND aip.total > 0 " + query_z + "\
                        GROUP BY\
                            a.id,\
                            i.partner_id,\
                            i.lead_id,\
                            aip.date_pay,\
                            aip.total\
                    ) x")
        return cr.dictfetchall()

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_act_report')
        cr.execute('''
            create or replace view account_act_report as (
                SELECT
                    row_number() over() as id,
                    to_char(NOW(), 'YYYY-MM-DD') date_end,
                    to_char(NOW(), 'YYYY-MM-DD') date_start,
                    x.*
                FROM (SELECT
                            a.id account_id,
                            i.partner_id partner_id,
                            i.lead_id lead_id,
                            aid.document_date document_date,
                            aid.document_cash document_cash,
                            NULL pay_date,
                            0.0 pay_total,
                            0.0 - COALESCE(aid.document_cash, 0) saldo
                        FROM
                            account_account a
                            LEFT JOIN account_invoice i
                                ON (i.account_id = a.id)
                            LEFT JOIN account_invoice_documents aid
                                ON (aid.invoice_id = i.id AND aid.name in ('completion_ru', 'completion_ua') AND aid.document_cash > 0)
                        WHERE
                            i.type='out_invoice' AND aid.document_cash > 0
                        GROUP BY
                            a.id,
                            i.partner_id,
                            i.lead_id,
                            aid.document_date,
                            aid.document_cash

                        UNION

                        SELECT
                            a.id account_id,
                            i.partner_id partner_id,
                            i.lead_id lead_id,
                            NULL document_date,
                            0.0 document_cash,
                            aip.date_pay pay_date,
                            aip.total pay_total,
                            COALESCE(aip.total, 0) saldo
                        FROM
                            account_account a
                            LEFT JOIN account_invoice i
                                ON (i.account_id = a.id)
                            LEFT JOIN account_invoice_pay aip
                                ON (aip.invoice_id = i.id AND aip.total > 0)
                        WHERE
                            i.type='out_invoice' AND aip.total > 0
                        GROUP BY
                            a.id,
                            i.partner_id,
                            i.lead_id,
                            aip.date_pay,
                            aip.total
                    ) x
            )
        ''')

accountActReport()