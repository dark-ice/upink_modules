# coding=utf-8
__author__ = 'andrey'
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportPlanning(Model):
    _name = 'day.report.planning'
    _description = u'Ежедневные отчеты - Планирование'
    _auto = False
    _order = 'date'

    def _fact_per(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['fact_total'], context):
            result = 0
            try:
                result = 365000 / record['fact_total']
            except:
                pass

            res[record['id']] = result
        return res

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'date': fields.date('Дата'),

        'week_number': fields.integer('Номер недели', group_operator="avg"),

        'plan_work': fields.float('Работа'),
        'plan_work_account': fields.float('Работа (счета)'),

        'plan_calling': fields.float('Привлечение'),
        'plan_calling_account': fields.float('Привлечение (счета)'),

        'plan_dev': fields.float('Развитие'),
        'plan_dev_account': fields.float('Развитие (счета)'),

        'plan_total': fields.float('Планы: всего'),
        'plan_per': fields.float('% плана'),

        'fact_work': fields.float('Работа'),
        'fact_calling': fields.float('Привлечение'),
        'fact_dev': fields.float('Развитие'),
        #'fact_per': fields.float('Факты: % плана'),
        'fact_per': fields.function(
            _fact_per,
            type='float',
            digits=(10, 2),
            string='Факты: % плана'
        ),
        'fact_total': fields.float('Факты: всего'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'day_report_planning')
        cr.execute("""
            create or replace view day_report_planning as (
                SELECT
                  row_number() over() as id,
                  to_char(x.date, 'YYYY-MM-DD') date_end,
                  to_char(x.date, 'YYYY-MM-DD') date_start,
                  x.date,
                  extract(week FROM x.date) week_number,
                  x.plan_work,
                  x.plan_work_account,
                  x.plan_calling,
                  x.plan_calling_account,
                  x.plan_dev,
                  x.plan_dev_account,
                  x.plan_work + x.plan_calling + plan_dev plan_total,
                  (x.plan_work + x.plan_calling + plan_dev)/365000 plan_per,
                  y.fact_work,
                  y.fact_dev,
                  y.fact_calling,
                  y.fact_total
                FROM (
                  SELECT
                    r.date,
                    max(case when r.section_id=8 then r.plan else 0 end) plan_work,
                    sum(case when u.context_section_id=8 AND u.context_section_id=r.section_id then i.total_ye else 0 end) plan_work_account,
                    max(case when r.section_id=7 then r.plan else 0 end) plan_calling,
                    sum(case when u.context_section_id=7 AND u.context_section_id=r.section_id then i.total_ye else 0 end) plan_calling_account,
                    max(case when r.section_id=9 then r.plan else 0 end) plan_dev,
                    sum(case when u.context_section_id=9 AND u.context_section_id=r.section_id then i.total_ye else 0 end) plan_dev_account
                  FROM day_report_plan r
                    LEFT JOIN account_invoice i on (r.date=i.plan_paid_date)
                    LEFT JOIN res_users u on (u.id=i.user_id)
                  GROUP BY r.date
                ) x LEFT JOIN (
                  SELECT
                    r.date,
                    sum(case when u.context_section_id=8 AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_work,
                    sum(case when u.context_section_id=7 AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_calling,
                    sum(case when u.context_section_id=9 AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_dev,
                    sum(case when u.context_section_id in (8, 7, 9) AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_total
                  FROM day_report_plan r
                    LEFT JOIN account_invoice i on (r.date=i.paid_date)
                    LEFT JOIN res_users u on (u.id=i.user_id)
                  GROUP BY r.date
                ) y on (x.date=y.date)
                GROUP BY x.date,
                  x.plan_work,
                  x.plan_work_account,
                  x.plan_calling,
                  x.plan_calling_account,
                  x.plan_dev,
                  x.plan_dev_account,
                  plan_total,
                  plan_per,
                  y.fact_work,
                  y.fact_dev,
                  y.fact_calling,
                  y.fact_total
            )""")

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for item in domain:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='
            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
                item[2] = "{date} 23:59:59".format(date=item[2],)

        return super(ReportPlanning, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)
ReportPlanning()