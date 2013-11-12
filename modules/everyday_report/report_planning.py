# coding=utf-8
__author__ = 'andrey'
from datetime import datetime
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportPlanning(Model):
    _name = 'day.report.planning'
    _description = u'Ежедневные отчеты - Планирование'
    _auto = False
    _order = 'date'

    def _sum(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['date'], context):
            start_date = datetime.strptime(record['date'], "%Y-%m-%d")
            f_ids = self.search(cr, uid, [('date', '<=', record['date']), ('date', '>=', start_date.strftime('%Y-%m-01'))])
            l = zip(*[(r['plan_total'], r['fact_total']) for r in self.read(cr, uid, f_ids, ['plan_total', 'fact_total'], context)])
            plan = sum(l[0])
            fact = sum(l[1])

            try:
                period = self.pool.get('kpi.period').get_by_date(cr, start_date)
                kpi_ids = self.pool.get('kpi.kpi').search(cr, 1, [('employee_id', '=', 10), ('period_id', '=', period.id)])
                mbo_ids = self.pool.get('kpi.mbo').search(cr, 1, [('kpi_id', 'in', kpi_ids), ('name', '=', 347)])
                mbo = self.pool.get('kpi.mbo').read(cr, 1, mbo_ids[0], ['plan'])
                plan_per = (plan / mbo['plan']) * 100
                fact_per = (fact / mbo['plan']) * 100
                plan_f = mbo['plan']
            except:
                plan_per = 0.0
                fact_per = 0.0
                plan_f = 0.0

            res[record['id']] = {
                'plan': plan,
                'fact': fact,
                'plan_per': plan_per,
                'fact_per': fact_per,
                'plan_f': plan_f
            }
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

        'plan': fields.function(
            _sum,
            type='float',
            multi="calc_planning",
            string='Планы: всего получение'
        ),
        'plan_per': fields.function(
            _sum,
            type='float',
            digits=(10, 2),
            multi="calc_planning",
            string='План'
        ),
        'plan_f': fields.function(
            _sum,
            type='float',
            digits=(10, 2),
            multi="calc_planning",
            string='Планы: % плана'
        ),

        'fact_work': fields.float('Работа'),
        'fact_calling': fields.float('Привлечение'),
        'fact_dev': fields.float('Развитие'),
        'fact_per': fields.function(
            _sum,
            type='float',
            digits=(10, 2),
            multi="calc_planning",
            string='Факты: % плана'
        ),
        'fact_total': fields.float('Факты: всего'),
        'fact': fields.function(
            _sum,
            type='float',
            multi="calc_planning",
            string='Факты: всего получение'
        ),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'day_report_planning')
        cr.execute("""
            create or replace view day_report_planning as (
                SELECT
                  row_number() over() as id,
                  to_char(r.date, 'YYYY-MM-DD') date_end,
                  to_char(r.date, 'YYYY-MM-DD') date_start,
                  r.date,
                  extract(week FROM r.date) week_number,
                  r.plan_work,
                  r.plan_work_account,
                  r.plan_calling,
                  r.plan_calling_account,
                  r.plan_dev,
                  r.plan_dev_account,
                  r.plan_work + r.plan_calling + r.plan_dev plan_total,
                  fact_work,
                  fact_calling,
                  fact_dev,
                  fact_work + fact_calling + fact_dev fact_total
                FROM (
                  SELECT
                    r.date,
                    sum(case when r.section_id=8 then r.plan else 0 end) plan_work,
                    sum(case when r.section_id=7 then r.plan else 0 end) plan_calling,
                    sum(case when r.section_id=9 then r.plan else 0 end) plan_dev,
                    i.plan_calling_account,
                    i.plan_dev_account,
                    i.plan_work_account,
                    fact_work_part fact_work,
                    fact_calling_part fact_calling,
                    fact_dev_part fact_dev
                  FROM day_report_plan r
                    LEFT JOIN (
                      SELECT
                        i.plan_paid_date,
                        sum(case when u.context_section_id=8 then i.total_ye else 0 end) plan_work_account,
                        sum(case when u.context_section_id=7 then i.total_ye else 0 end) plan_calling_account,
                        sum(case when u.context_section_id=9 or i.user_id=14 then i.total_ye else 0 end) plan_dev_account
                      FROM account_invoice i
                      LEFT JOIN res_users u on (u.id=i.user_id)
                      WHERE i.user_id <> 170
                      GROUP BY i.plan_paid_date
                    ) i on (r.date=i.plan_paid_date)
                    LEFT JOIN (
                      SELECT
                        ip.date_pay,
                        sum(case when u.context_section_id=8 then ipl.factor else 0 end) fact_work_part,
                        sum(case when u.context_section_id=7 then ipl.factor else 0 end) fact_calling_part,
                        sum(case when u.context_section_id=9 or i.user_id=14 then ipl.factor else 0 end) fact_dev_part
                      FROM
                        account_invoice_pay ip
                        LEFT JOIN account_invoice i on (i.id=ip.invoice_id)
                        LEFT JOIN account_invoice_pay_line ipl on (ipl.invoice_pay_id=ip.id)
                        LEFT JOIN res_users u on (u.id=i.user_id)
                      GROUP BY ip.date_pay
                    ) i3 on (i3.date_pay=r.date)
                  GROUP BY
                    r.date,
                    i.plan_calling_account,
                    i.plan_dev_account,
                    i.plan_work_account,
                    fact_work_part,
                    fact_calling_part,
                    fact_dev_part
                  ) r
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