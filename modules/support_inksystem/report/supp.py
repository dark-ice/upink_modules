# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class SuppReport(Model):
    _name = "supp.sale.report"
    _description = u"Отчет по квитанциям"
    _auto = False
    _rec_name = 'city_id'

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'city_id': fields.many2one(
            'supp.city.stage',
            'Город',
            select=True,
            readonly=True,
            states={
                'draft': [('readonly', False), ('required', True)],
                'repiar': [('readonly', False), ('required', True)]
            },
            help='Город'),

        'create_all': fields.char('Принято', size=200),
        'ready_all': fields.char('Отремонтировано', size=200),
        'putup_all': fields.char('Выдано', size=200),

        'd1': fields.integer("Старше 14 дней в ремонте (за период)"),
        'd2': fields.integer("Старше 14 дней в ремонте (тек)"),
        'd3': fields.integer("Больше 3-х мес не выдано"),
        'c_date': fields.integer("Больше 2-х дней без звонка"),
        'cw_date': fields.integer("Больше 2-х дней без звонка (тек)"),
    }

    _order = 'city_id'

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        return super(SuppReport, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)

    def get_records(self, cr, date_start, date_end, city):
        create = []
        ready = []
        putup = []
        query_create = ''
        query_ready = ''
        query_putup = ''
        query_city = ''

        if date_start:
            create.append(" s.create_date >='%s'::timestamp" % date_start)
            ready.append(" s.ready_date >='%s'::timestamp" % date_start)
            putup.append(" s.putup_date >='%s'::timestamp" % date_start)
        if date_end:
            create.append(" s.create_date <='%s'::timestamp" % date_end)
            ready.append(" s.ready_date <='%s'::timestamp" % date_end)
            putup.append(" s.putup_date <='%s'::timestamp" % date_end)

        if create:
            query_create = ' AND '.join(create)
        else:
            query_create = 's.create_date IS NOT NULL'
        if ready:
            query_ready = ' AND '.join(ready)
        else:
            query_ready = 's.ready_date IS NOT NULL'
        if putup:
            query_putup = ' AND '.join(putup)
        else:
            query_putup = 's.putup_date IS NOT NULL'

        if city:
            query_city += ' WHERE s.city_id =%s' % city

        cr.execute("SELECT\
                  row_number() over() as id,\
                  date_end,\
                  date_start,\
                  city_id,\
                  concat(c_create, '(', case when c_create=0 then 0 else cw_create * 100/c_create end, '%)') create_all,\
                  concat(c_ready, '(',case when c_ready=0 then 0 else cw_ready * 100/c_ready end, '%)') ready_all,\
                  concat(c_putup, '(',case when c_putup=0 then 0 else cw_putup * 100/c_putup end, '%)') putup_all,\
                  d1,\
                  d2,\
                  d3,\
                  c_date,\
                  cw_date\
                FROM (\
                  SELECT\
                    city_id,\
                    to_char(max(s.create_date), 'YYYY-MM-DD') date_end,\
                    to_char(min(s.create_date), 'YYYY-MM-DD') date_start,\
                    sum(case when " + query_create + " then 1 else 0 end) c_create,\
                    sum(case when " + query_create + " and type_supp='warranty' then 1 else 0 end) cw_create,\
                    sum(case when " + query_ready + " then 1 else 0 end) c_ready,\
                    sum(case when " + query_ready + " and type_supp='warranty' then 1 else 0 end) cw_ready,\
                    sum(case when " + query_putup + " then 1 else 0 end) c_putup,\
                    sum(case when " + query_putup + " and type_supp='warranty' then 1 else 0 end) cw_putup,\
                    sum(case when EXTRACT(DAY FROM COALESCE(s.ready_date, now() at time zone 'UTC') - s.create_date) > 14 AND s.ready_date IS NOT NULL AND " + query_ready + " then 1 else 0 end) d1,\
                    sum(case when EXTRACT(DAY FROM COALESCE(s.ready_date, now() at time zone 'UTC') - s.create_date) > 14 and state in ('draft', 'repiar') then 1 else 0 end) d2,\
                    sum(case when s.state = 'repiar_end' and EXTRACT(DAY FROM now() at time zone 'UTC' - s.ready_date)/30 > 3 then 1 else 0 end) d3,\
                    sum(case when " + query_ready + " and EXTRACT(DAY FROM COALESCE(n.c_date, now() at time zone 'UTC') - s.ready_date) > 2 then 1 else 0 end) c_date,\
                    sum(case when " + query_ready + " and s.state = 'repiar_end' and EXTRACT(DAY FROM COALESCE(n.c_date, now() at time zone 'UTC') - s.ready_date) > 2 then 1 else 0 end) cw_date\
                  FROM\
                    supp_sale s\
                    LEFT JOIN (SELECT min(create_date) c_date, supp_id FROM supp_sale_notes GROUP BY supp_id) n on (n.supp_id=s.id) " + query_city + "\
                  GROUP BY\
                    city_id\
                ) a")

        return cr.dictfetchall()

    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        date_start = context.get("date_start", False)
        date_end = context.get("date_end", False)
        city = context.get("city_id", False)
        return self.get_records(cr, date_start, date_end, city)

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        city_id = [item for item in args if item[0] == 'city_id']
        date_start = [item for item in args if item[0] == 'date_start']
        date_end = [item for item in args if item[0] == 'date_end']
        if date_start:
            context['date_start'] = date_start[0][2]
        if date_end:
            context['date_end'] = date_end[0][2]
        if city_id:
            context['city_id'] = city_id[0][2]

        return super(SuppReport, self).search(cr, user, [], offset, limit, order, context, count)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'supp_sale_report')
        cr.execute("""
            create or replace view supp_sale_report as (
                SELECT
                  row_number() over() as id,
                  date_end,
                  date_start,
                  city_id,
                  concat(c_create, '(', case when c_create=0 then 0 else cw_create * 100/c_create end, '%)') create_all,
                  concat(c_ready, '(',case when c_ready=0 then 0 else cw_ready * 100/c_ready end, '%)') ready_all,
                  concat(c_putup, '(',case when c_putup=0 then 0 else cw_putup * 100/c_putup end, '%)') putup_all,
                  d1,
                  d2,
                  d3,
                  c_date,
                  cw_date
                FROM (
                  SELECT
                    city_id,
                    to_char(max(s.create_date), 'YYYY-MM-DD') date_end,
                    to_char(min(s.create_date), 'YYYY-MM-DD') date_start,
                    sum(case when s.create_date IS NOT NULL then 1 else 0 end) c_create,
                    sum(case when s.create_date IS NOT NULL and type_supp='warranty' then 1 else 0 end) cw_create,

                    sum(case when s.ready_date IS NOT NULL then 1 else 0 end) c_ready,
                    sum(case when s.ready_date IS NOT NULL and type_supp='warranty' then 1 else 0 end) cw_ready,

                    sum(case when s.putup_date IS NOT NULL then 1 else 0 end) c_putup,
                    sum(case when s.putup_date IS NOT NULL and type_supp='warranty' then 1 else 0 end) cw_putup,

                    sum(case when EXTRACT(DAY FROM COALESCE(s.ready_date, now() at time zone 'UTC') - s.create_date) > 14 AND s.ready_date IS NOT NULL then 1 else 0 end) d1,
                    sum(case when EXTRACT(DAY FROM COALESCE(s.ready_date, now() at time zone 'UTC') - s.create_date) > 14 and state in ('draft', 'repiar') then 1 else 0 end) d2,

                    sum(case when s.state = 'repiar_end' and EXTRACT(DAY FROM now() at time zone 'UTC' - s.ready_date)/30 > 3 then 1 else 0 end) d3,
                    sum(case when s.ready_date IS NOT NULL and EXTRACT(DAY FROM COALESCE(n.c_date, now() at time zone 'UTC') - s.ready_date) > 2 then 1 else 0 end) c_date,
                    sum(case when s.ready_date IS NOT NULL and s.state = 'repiar_end' and EXTRACT(DAY FROM COALESCE(n.c_date, now() at time zone 'UTC') - s.ready_date) > 2 then 1 else 0 end) cw_date
                  FROM
                    supp_sale s
                    LEFT JOIN (SELECT min(create_date) c_date, supp_id FROM supp_sale_notes GROUP BY supp_id) n on (n.supp_id=s.id)
                  GROUP BY
                    city_id
                ) a
            )
        """)

SuppReport()