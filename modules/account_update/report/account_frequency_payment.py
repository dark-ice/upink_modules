# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class accountFrequencyPayment(Model):
    _name = "account.frequency.payment"
    _description = u"Отчет по частоте оплат"
    _auto = False
    _rec_name = 'number'

    _columns = {
        'date_start': fields.date(u'с', select="1"),
        'date_end': fields.date(u'по', select="1"),

        'lead_id': fields.many2one('crm.lead', u'Кандидат', readonly=True),
        'partner_id': fields.many2one('res.partner', u'Партнер', readonly=True),
        'number': fields.char(u"Номер", size=10, readonly=True),
        'total_dol': fields.float(u'Сумма платежа в $', digits=(10, 2), readonly=True),
        'pay_date': fields.date(u'Дата платежа', readonly=True),
        'user_id': fields.many2one('res.users', u'Автор', select="1",),
        'pay_total': fields.float(u'Сумма платежа', digits=(10, 2), readonly=True),
        'service_id': fields.many2one('brief.services.stage', u'Услуга', readonly=True),
        'pay_number': fields.integer(u'Номер платежа'),
        'count_days': fields.integer(u'Кол-во дней с последней оплаты'),
        'division': fields.char(u'Направление', size=250),
    }

    _order = 'number desc'

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        user_id = [item for item in domain if item[0] == 'user_id']
        date_start = [item for item in domain if item[0] == 'date_start']
        date_end = [item for item in domain if item[0] == 'date_end']

        new_domain = []
        if user_id:
            new_domain.append(user_id[0])

        if date_start:
            date_s = ('pay_date', '>=', date_start[0][2])
            new_domain.append(date_s)

        if date_end:
            date_e = ('pay_date', '<=', date_end[0][2])
            new_domain.append(date_e)

        return super(accountFrequencyPayment, self).read_group(cr, uid, new_domain, fields, groupby, offset, limit, context, orderby)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_frequency_payment')
        cr.execute("""
            create or replace view account_frequency_payment as (
                SELECT
                     row_number() over() as id,
                     i.user_id user_id,
                     i.number number,
                     i.partner_id partner_id,
                     i.lead_id lead_id,
                     to_char(NOW(), 'YYYY-MM-DD') date_end,
                     to_char(NOW(), 'YYYY-MM-DD') date_start,
                     il.service_id service_id,
                     ipl.name pay_total,
                     ipl.name / i.rate total_dol,
                     ip.name pay_number,
                     ip.date_pay pay_date,
                     current_date - ip.date_pay::date count_days,
                     bss.direction division
                FROM
                    account_invoice i
                        left join account_invoice_line il on (il.invoice_id=i.id)
                        left join account_invoice_pay_line ipl on (ipl.invoice_id=i.id AND ipl.service_id=il.service_id)
                        left join account_invoice_pay ip on (ipl.invoice_pay_id=ip.id AND ip.name=(SELECT max(ip1.name)
                                            FROM account_invoice_pay ip1
                                              left join account_invoice_pay_line ipl1 on (ipl1.invoice_pay_id=ip1.id)
                                            WHERE ip1.invoice_id=i.id AND ipl1.service_id=il.service_id
                                            GROUP BY ip1.invoice_id, ipl1.service_id) AND ip.invoice_id=i.id)
                        left join brief_services_stage bss on (bss.id=il.service_id)
                        left join res_groups g on (g.id=bss.leader_group_id)
                WHERE
                    i.type='out_invoice' AND ip.date_pay IS NOT NULL AND current_date - ip.date_pay::date < 90
                GROUP BY
                    i.user_id,
                    i.number,
                    il.service_id,
                    i.partner_id,
                    i.lead_id,
                    i.rate,
                    ipl.name,
                    ip.name,
                    ip.date_pay,
                    g.name,
                    bss.direction
            )
        """)

accountFrequencyPayment()