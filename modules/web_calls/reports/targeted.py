# coding=utf-8
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model

__author__ = 'andrey'


class TargetedCalls(Model):
    _name = "web.calls.targeted.report"
    _description = u"Отчет по целевым звонкам"
    _auto = False

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'call_date': fields.date('Дата звонка'),
        'responsible_id': fields.many2one('res.users', 'Менеджер'),
        'sale': fields.integer('Продажа'),
        'consultation': fields.integer('Консультация'),
        'no_product': fields.integer('Запрос на отсутствующий товар'),
        'no_product_str': fields.char('Запрос на отсутствующий товар', size=250),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'web_calls_targeted_report')
        cr.execute("""
            create or replace view web_calls_targeted_report as (
                SELECT
                    row_number() over() as id,
                    to_char(call_date, 'YYYY-MM-DD') date_end,
                    to_char(call_date, 'YYYY-MM-DD') date_start,
                    call_date,
                    responsible_id,
                    no_product no_product_str,
                    case when call_type='sale' then 1 else 0 end sale,
                    case when call_type='consultation' then 1 else 0 end consultation,
                    case when call_type='no_product' then 1 else 0 end no_product
                FROM web_calls WHERE call_type IN ('sale', 'consultation', 'no_product') and incoming_call = True
            )""")

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for item in domain:
            if item[0] == 'date_start':
                item[0] = 'call_date'
                item[1] = '>='
            if item[0] == 'date_end':
                item[0] = 'call_date'
                item[1] = '<='
                item[2] = "{date} 23:59:59".format(date=item[2],)

        return super(TargetedCalls, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)


TargetedCalls()
