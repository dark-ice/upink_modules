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

    def _per(self, cr, uid, ids, name, arg, context=None):
        res = {}
        field = name[:-4]
        for record in self.read(cr, uid, ids, [field], context):
            res[record['id']] = (record[field] / 365000) * 100
        return res

    def _sum(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['date'], context):
            start_date = datetime.strptime(record['date'], "%Y-%m-%d")
            f_ids = self.search(cr, uid, [('date', '<=', record['date']), ('date', '>=', start_date.strftime('%Y-%m-01'))])
            l = zip(*[(r['plan_total'], r['fact_total']) for r in self.read(cr, uid, f_ids, ['plan_total', 'fact_total'], context)])
            plan = sum(l[0])
            fact = sum(l[1])
            try:
                fact_per = 365000 / fact
            except:
                fact_per = 0.0
            res[record['id']] = {
                'plan': plan,
                'fact': fact,
                'plan_per': (plan / 365000) * 100,
                'fact_per': fact_per,
            }
        return res

    def _calc(self, cr, uid, ids, name, arg, context=None):
        res = {}
        line_pool = self.pool.get('account.invoice.line')
        pay_pool = self.pool.get('account.invoice.pay')
        for record in self.read(cr, uid, ids, ['date'], context):
            plan_per = 0.0
            work_ids = []
            calling_ids = []
            dev_ids = []

            invoice_full_ids = self.pool.get('account.invoice').search(cr, 1, [('type', '=', 'out_invoice'), ('paid_date', '=', record['date'])])
            for invoice in self.pool.get('account.invoice').read(cr, 1, invoice_full_ids, ['user_id']):
                section_id = self.pool.get('res.users').read(cr, 1, invoice['user_id'][0], ['context_section_id'])['context_section_id'][0]
                if section_id == 8:
                    work_ids.append(invoice['id'])
                elif section_id == 7:
                    calling_ids.append(invoice['id'])
                elif section_id == 9:
                    dev_ids.append(invoice['id'])

            work_line_ids = line_pool.search(cr, 1, [('invoice_id', 'in', work_ids)])
            fact_work = sum(l['factor'] for l in line_pool.read(cr, 1, work_line_ids, ['factor']))
            calling_line_ids = line_pool.search(cr, 1, [('invoice_id', 'in', calling_ids)])
            fact_calling = sum(l['factor'] for l in line_pool.read(cr, 1, calling_line_ids, ['factor']))
            dev_line_ids = line_pool.search(cr, 1, [('invoice_id', 'in', dev_ids)])
            fact_dev = sum(l['factor'] for l in line_pool.read(cr, 1, dev_line_ids, ['factor']))

            work_pay_ids = []
            calling_pay_ids = []
            dev_pay_ids = []

            pay_ids = pay_pool.search(cr, 1, [('invoice_id', '!=', False), ('invoice_id', 'not in', invoice_full_ids), ('date_pay', '=', record['date'])])
            for pay in pay_pool.read(cr, 1, pay_ids, ['invoice_id']):
                section_id = self.pool.get('res.users').read(cr, 1, self.pool.get('account.invoice').read(cr, 1, pay['invoice_id'][0], ['user_id'])['user_id'][0], ['context_section_id'])['context_section_id'][0]
                if section_id == 8:
                    work_pay_ids.append(pay['id'])
                elif section_id == 7:
                    calling_pay_ids.append(pay['id'])
                elif section_id == 9:
                    dev_pay_ids.append(pay['id'])

            work_pay_line_ids = pay_pool.search(cr, 1, [('invoice_id', 'in', work_pay_ids)])
            fact_work += sum(l['name'] for l in pay_pool.read(cr, 1, work_pay_line_ids, ['name']))
            calling_pay_line_ids = pay_pool.search(cr, 1, [('invoice_id', 'in', calling_pay_ids)])
            fact_calling += sum(l['name'] for l in pay_pool.read(cr, 1, calling_pay_line_ids, ['name']))
            dev_pay_line_ids = pay_pool.search(cr, 1, [('invoice_id', 'in', dev_pay_ids)])
            fact_dev += sum(l['name'] for l in pay_pool.read(cr, 1, dev_pay_line_ids, ['name']))

            fact_total = fact_work + fact_calling + fact_dev

            try:
                fact_per = 365000 / fact_total
            except:
                fact_per = 0.0

            res[record['id']] = {
                'fact_work': fact_work,
                'fact_calling': fact_calling,
                'fact_dev': fact_dev,
                'fact_per': fact_per,
                'fact_total': fact_total,
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
                  (r.plan_work + r.plan_calling + r.plan_dev)/365000 plan_per,
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
                        sum(case when u.context_section_id=9 then i.total_ye else 0 end) plan_dev_account
                      FROM account_invoice i
                      LEFT JOIN res_users u on (u.id=i.user_id)
                      GROUP BY i.plan_paid_date
                    ) i on (r.date=i.plan_paid_date)
                    LEFT JOIN (
                      SELECT
                        ip.date_pay,
                        sum(case when u.context_section_id=8 then ipl.factor else 0 end) fact_work_part,
                        sum(case when u.context_section_id=7 then ipl.factor else 0 end) fact_calling_part,
                        sum(case when u.context_section_id=9 then ipl.factor else 0 end) fact_dev_part
                      FROM
                        account_invoice_pay ip
                        LEFT JOIN account_invoice i on (i.id=ip.invoice_id AND i.paid_date is null)
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