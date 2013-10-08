# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class accountBalanceManager(Model):
    _name = "account.balance.manager"
    _description = u"Отчет по оплатам"
    _auto = False
    _rec_name = 'number'

    _columns = {
        'date_start': fields.date('с', select="1"),
        'date_end': fields.date('по', select="1"),

        #'lead_id': fields.many2one('crm.lead', 'Кандидат', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', readonly=True),
        'partner_name': fields.char('Сайт партнера', size=200),
        'partner_urname': fields.char('Юридическое наименование партнера', size=200),
        'number': fields.char('Номер', size=10, readonly=True),
        'date_invoice': fields.date('Дата счета', readonly=True),
        'total': fields.float('Сумма счета в валюте счета', digits=(10, 2), readonly=True),
        'pay_id': fields.integer('Номер платежа', readonly=True),
        'pay_date': fields.date('Дата платежа', readonly=True),
        'user_id': fields.many2one('res.users', 'Автор', select="1",),

        'pay_total': fields.float('Сумма платежа', digits=(10, 2), readonly=True),
        'pay_dol': fields.float('Сумма платежа в $', digits=(10, 2), readonly=True),
        'currency_rate': fields.float('Курс', digits=(10, 4), readonly=True),
        'total_dol': fields.float('Сумма в $', digits=(10, 2), readonly=True),
        'service_id': fields.many2one('brief.services.stage', 'Услуга', readonly=True),
        'pay_line_name': fields.float('Сумма платежа по услуге', digits=(10, 2), readonly=True),
        'pay_line_name_dol': fields.float('Сумма платежа по услуге в $', digits=(10, 2), readonly=True),
        'division': fields.char('Направление', size=250),
        'leader_group_id': fields.many2one(
            'res.groups',
            'Группа руководителя операционного направления'
        ),
        'card_id': fields.many2one(
            'account.invoice.card',
            'Касса/банк/кошелек'
        ),
        'section_id': fields.many2one('crm.case.section', 'Sales Team'),
    }

    _order = 'number desc'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        for arg in args:
            if arg[0] == 'date_start':
                arg[1] = '>='
            if arg[0] == 'date_end':
                arg[1] = '<='
        return super(accountBalanceManager, self).search(cr, user, args, offset, limit, order, context, count)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for arg in domain:
            if arg[0] == 'date_start':
                arg[1] = '>='
            if arg[0] == 'date_end':
                arg[1] = '<='
        return super(accountBalanceManager, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_balance_manager')
        cr.execute("""
            create or replace view account_balance_manager as (
                SELECT
                  row_number() over() as id,
                  to_char(ip.date_pay, 'YYYY-MM-DD') date_end,
                  to_char(ip.date_pay, 'YYYY-MM-DD') date_start,
                  i.user_id user_id,
                  i.date_invoice date_invoice,
                  i.rate currency_rate,
                  i.number number,
                  i.partner_id partner_id,
                  p.name partner_name,
                  p.ur_name partner_urname,
                  il.specialist_id,
                  il.service_id,
                  il.direction,
                  il.leader_group_id,
                  il.price_currency total,
                  il.price_unit total_dol,
                  u.context_section_id section_id,
                  ip.card_id,
                  ip.total pay_total,
                  ip.total / i.rate pay_dol,
                  ip.pay_line_name,
                  ip.pay_line_name / i.rate pay_line_name_dol
                FROM
                  account_invoice i
                  left join res_users u on (u.id=i.user_id)
                  left join res_partner p on (p.id=i.partner_id)
                  left join (
                    SELECT
                      b.specialist_id,
                      il.invoice_id,
                      il.service_id,
                      il.price_currency,
                      il.price_unit,
                      bss.direction,
                      bss.leader_group_id
                    FROM account_invoice_line il
                      left join brief_main b on (b.id=il.brief_id)
                      left join brief_services_stage bss on (bss.id=il.service_id)
                  ) il on (il.invoice_id=i.id)
                  left join (
                    SELECT
                      ip.invoice_id,
                      ip.total,
                      ip.date_pay,
                      ip.card_id,
                      sum(ipl.name) pay_line_name
                    FROM account_invoice_pay ip
                      left join account_invoice_pay_line ipl on (ipl.invoice_pay_id=ip.id)
                    GROUP BY ip.invoice_id, ip.total, ip.date_pay, ip.card_id
                  ) ip on (ip.invoice_id=i.id)
                WHERE
                  i.type='out_invoice' AND i.date_invoice IS NOT NULL AND ip.total IS NOT NULL
            )
        """)

accountBalanceManager()