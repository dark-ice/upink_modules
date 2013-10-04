# coding=utf-8
from datetime import date, datetime
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model, TransientModel


class ReportSourcePlan(Model):
    _name = 'day.report.source.plan'
    _description = u'Ежедневные отчеты - Источники - Планы'
    _rec_name = 'section_id'
    _order = 'period_year desc, period_month desc, section_id'

    _columns = {
        'uid': fields.many2one(
            'res.users',
            'Автор',
            readonly=True
        ),
        'section_id': fields.many2one(
            'crm.case.section',
            'Поднаправление',
            domain=[('id', 'child_of', [6])], required=True
        ),
        'plan': fields.float('План'),
        'period_month': fields.selection(
            (
                ('1', 'Январь'),
                ('2', 'Февраль'),
                ('3', 'Март'),
                ('4', 'Апрель'),
                ('5', 'Май'),
                ('6', 'Июнь'),
                ('7', 'Июль'),
                ('8', 'Август'),
                ('9', 'Сентябрь'),
                ('10', 'Октябрь'),
                ('11', 'Ноябрь'),
                ('12', 'Декабрь'),
            ), "Месяц", required=True
        ),
        'period_year': fields.selection(
            (
                ('2012', '2012'),
                ('2013', '2013'),
                ('2014', '2014'),
                ('2015', '2015'),
                ('2016', '2016'),
                ('2017', '2017'),
                ('2018', '2018'),
                ('2019', '2019'),
                ('2020', '2020'),
            ), 'Год', required=True),
    }

    _defaults = {
        'uid': lambda s, cr, u, ctxt: u,
        'section_id': lambda s, cr, u, ctxt: ctxt.get('context_section_id', False),
        'period_year': lambda *a: str(date.today().year),
        'period_month': lambda *a: str(date.today().month),
    }
ReportSourcePlan()


class ReportSource(Model):
    _name = 'day.report.source'
    _description = u'Ежедневные отчеты - Источники'
    _auto = False
    _order = 'date'

    def _fact(self, cr, uid, ids, name, arg, context=None):
        res = {}
        field = "{name}_s".format(name=name,)
        for record in self.read(cr, uid, ids, ['date'], context):
            start_date = datetime.strptime(record['date'], "%Y-%m-%d")
            f_ids = self.search(cr, uid, [('date', '<=', record['date']), ('date', '>=', start_date.strftime('%Y-%m-01'))])
            res[record['id']] = sum(r[field] for r in self.read(cr, uid, f_ids, [field], context))
        return res

    def _part(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        fact = name.replace('part', 'fact')
        for record in self.read(cr, uid, ids, [fact, 'fact_total'], context):
            try:
                result = record[fact] * 100 / record['fact_total']
            except ZeroDivisionError:
                result = 0
            res[record['id']] = result
        return res

    def _per(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        fact = name.replace('per', 'fact')
        plan = name.replace('per', 'plan')
        for record in self.read(cr, uid, ids, [fact, plan], context):
            try:
                result = record[fact] * 100 / record[plan]
            except ZeroDivisionError:
                result = 0
            res[record['id']] = result
        return res

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'date': fields.date('Дата'),

        'plan_dev': fields.float('Развитие план'),
        'fact_dev_s': fields.float('Развитие факт'),
        'fact_dev': fields.function(
            _fact,
            type='float',
            string='Развитие  факт'
        ),
        'part_dev': fields.function(
            _part,
            type='float',
            string='Развитие доля в общем'
        ),
        'per_dev': fields.function(
            _per,
            type='float',
            string='Развитие процент выполнения'
        ),

        'plan_calling': fields.float('Привлечение план'),
        'fact_calling_s': fields.float('Привлечение факт'),
        'fact_calling': fields.function(
            _fact,
            type='float',
            string='Привлечение  факт'
        ),
        'part_calling': fields.function(
            _part,
            type='float',
            string='Привлечение доля в общем'
        ),
        'per_calling': fields.function(
            _per,
            type='float',
            string='Привлечение процент выполнения'
        ),

        'plan_cold': fields.float('Холодные звонки план'),
        'fact_cold_s': fields.float('Холодные звонки факт'),
        'fact_cold': fields.function(
            _fact,
            type='float',
            string='Холодные звонки факт'
        ),
        'part_cold': fields.function(
            _part,
            type='float',
            string='Холодные звонки доля в общем'
        ),
        'per_cold': fields.function(
            _per,
            type='float',
            string='Холодные звонки процент выполнения'
        ),

        'plan_marketing': fields.float('Маркетинг план'),
        'fact_marketing_s': fields.float('Маркетинг факт'),
        'fact_marketing': fields.function(
            _fact,
            type='float',
            string='Маркетинг факт'
        ),
        'part_marketing': fields.function(
            _part,
            type='float',
            string='Маркетинг доля в общем'
        ),
        'per_marketing': fields.function(
            _per,
            type='float',
            string='Маркетинг процент выполнения'
        ),

        'plan_moscow': fields.float('Москва план'),
        'fact_moscow_s': fields.float('Москва факт'),
        'fact_moscow': fields.function(
            _fact,
            type='float',
            string='Москва факт'
        ),
        'part_moscow': fields.function(
            _part,
            type='float',
            string='Москва доля в общем'
        ),
        'per_moscow': fields.function(
            _per,
            type='float',
            string='Москва процент выполнения'
        ),

        'plan_total': fields.float('Планы: всего'),
        'fact_total_s': fields.float('Факты: всего'),
        'fact_total': fields.function(
            _fact,
            type='float',
            string='Факты: всего'
        ),
        'per_total': fields.function(
            _per,
            type='float',
            string='Развитие процент выполнения'
        ),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'day_report_source')
        cr.execute("""
            create or replace view day_report_source as (
                SELECT
                  row_number() over() as id,
                  to_char(i.paid_date, 'YYYY-MM-DD') date_end,
                  to_char(i.paid_date, 'YYYY-MM-DD') date_start,
                  i.paid_date date,
                  sum(case when u.context_section_id=9 AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_dev_s,
                  sum(case when u.context_section_id in (7, 17, 18) AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_calling_s,
                  sum(case when u.context_section_id=7 AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_cold_s,
                  sum(case when u.context_section_id=17 AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_marketing_s,
                  sum(case when u.context_section_id=18 AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_moscow_s,
                  sum(case when u.context_section_id in (7, 9, 17, 18) AND u.context_section_id=r.section_id then case i.factor when 0 then i.total_ye else i.factor end else 0 end) fact_total_s,
                  max(case when r.section_id=9 then r.plan else 0 end) plan_dev,
                  max(case when r.section_id in (7, 17, 18) then r.plan else 0 end) plan_calling,
                  max(case when r.section_id=7 then r.plan else 0 end) plan_cold,
                  max(case when r.section_id=17 then r.plan else 0 end) plan_marketing,
                  max(case when r.section_id=18 then r.plan else 0 end) plan_moscow,
                  max(case when r.section_id in (7, 9, 17, 18) then r.plan else 0 end) plan_total
                FROM account_invoice i
                  LEFT JOIN res_users u on (u.id=i.user_id)
                  LEFT JOIN day_report_source_plan r on (
                    r.period_month::int=EXTRACT(MONTH FROM i.paid_date)
                    AND r.period_year::int=EXTRACT(YEAR FROM i.paid_date))
                WHERE paid_date is not NULL
                GROUP BY i.paid_date
            )""")

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        for item in args:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='
            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
                item[2] = "{date} 23:59:59".format(date=item[2],)
        return super(ReportSource, self).search(cr, user, args, offset, limit, order, context, count)


ReportSource()
