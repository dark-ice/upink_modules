# coding=utf-8
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model

__author__ = 'andrey'


class NonTargetedCalls(Model):
    _name = "web.calls.non.targeted.report"
    _description = u"Отчет по нецелевым звонкам"
    _auto = False

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'call_date': fields.date('Дата звонка'),
        'responsible_id': fields.many2one('res.users', 'Менеджер'),
        'total': fields.integer('Итого'),
        'qa': fields.integer('Тех.поддержка'),
        'ordr': fields.integer('Уточнения по оформленному заказу'),
        'atc': fields.integer('Проблема с АТС'),
        'number': fields.integer('Ошиблись номером'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'web_calls_non_targeted_report')
        cr.execute("""
            create or replace view web_calls_non_targeted_report as (
                SELECT
                    row_number() over() as id,
                    to_char(max(call_date), 'YYYY-MM-DD') date_end,
                    to_char(max(call_date), 'YYYY-MM-DD') date_start,
                    max(call_date) call_date,
                    responsible_id,
                    sum(case when call_type in ('qa', 'order', 'atc', 'number') then 1 else 0 end) total,
                    sum(case when call_type='qa' then 1 else 0 end) qa,
                    sum(case when call_type='order' then 1 else 0 end) ordr,
                    sum(case when call_type='atc' then 1 else 0 end) atc,
                    sum(case when call_type='number' then 1 else 0 end) number
                FROM web_calls WHERE call_type IN ('qa', 'order', 'atc', 'number') GROUP BY responsible_id, call_date::date
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

        return super(NonTargetedCalls, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)


NonTargetedCalls()
