# -*- coding: utf-8 -*-
import tools
from osv import fields, osv


class crmLeadATCReport(osv.osv):
    _name = "crm.lead.atc.report"
    _description = u"Отчет менеджера по привлечению партнеров"
    _auto = False
    _rec_name = 'responsible_user'

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'responsible_user': fields.many2one(
            'res.users',
            'Менеджер продаж',
            readonly=True,
            domain="[('groups_id','in',[47, 49])]"
        ),
        'responsible_user2': fields.many2one(
            'res.users',
            'Менеджер продаж',
            readonly=True,
            domain="[('groups_id','in',[47, 49])]"
        ),
        'name_manager': fields.char('Менеджер продаж', size=250, readonly=True),
        'callerid': fields.char('Внутренний номер', size=50, readonly=True),
        'time_of_coll': fields.char('Сумма разговора в часах', size=100, readonly=True),
        'count_calls': fields.integer('Количество звонков', readonly=True),
        'call': fields.char('Среднее время одного разговора', size=50, readonly=True),
        'count_briefs': fields.integer('Количество брифов', readonly=True),
        'budget': fields.integer("Планируемый бюджет руб/мес", readonly=True),
        'sum_rub': fields.integer("Сумма медиапалнов руб", readonly=True),
        'sum_dol': fields.integer("Сумма медиапалнов $", readonly=True),
        'sum_uah': fields.integer("Сумма медиапалнов грн", readonly=True),
    }

    _order = 'name_manager'

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        return super(crmLeadATCReport, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        user_id = [item for item in args if item[0] == 'responsible_user']
        date_start = [item for item in args if item[0] == 'date_start']
        date_end = [item for item in args if item[0] == 'date_end']
        if date_start:
            context['date_start'] = date_start[0][2]
        if date_end:
            context['date_end'] = date_end[0][2]
        if user_id:
            context['responsible_user'] = user_id[0][2]

        return super(crmLeadATCReport, self).search(cr, user, [], offset, limit, order, context, count)

    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        date_start = context.get("date_start", False)
        date_end = context.get("date_end", False)
        responsible = context.get("responsible_user", False)
        return self.get_records(cr, date_start, date_end, responsible)
        #return super(crmLeadATCReport, self).read(cr, user, ids, fields, context, load)

    def get_records(self, cr, date_start, date_end, responsible):
        query_x = ''
        query_z = ''
        if date_start:
            query_x += " AND c.date >='%s'::timestamp" % date_start
            query_z += " AND b.create_date >='%s'::timestamp" % date_start
        if date_end:
            query_x += " AND c.date <='%s'::timestamp" % date_end
            query_z += " AND b.create_date <='%s'::timestamp" % date_end
        if responsible:
            query_x += ' AND u.id =%s' % responsible
            query_z += ' AND u.id =%s' % responsible

        cr.execute("SELECT\
                    row_number() over() as id,\
                    x.*,\
                    COALESCE(z.responsible_user2, 0) responsible_user2,\
                    COALESCE(z.count_briefs, 0) count_briefs,\
                    COALESCE(z.budget, 0) budget,\
                    COALESCE(z.sum_rub, 0) sum_rub,\
                    COALESCE(z.sum_dol, 0) sum_dol,\
                    COALESCE(z.sum_uah, 0) sum_uah\
                FROM (\
                    SELECT\
                        u.name name_manager,\
                        u.id responsible_user,\
                        c.id_sphone callerid,\
                        count(c.id) as count_calls,\
                        to_char(sum(c.time_of_coll), 'HH24:MI:SS') time_of_coll,\
                        to_char(sum(c.time_of_coll) / count(c.id), 'HH24:MI:SS') as call\
                    FROM\
                        res_users u\
                            left join res_groups_users_rel g on (g.uid=u.id)\
                            left join crm_phonecall c on (c.id_sphone::int4=u.callerid)\
                    WHERE\
                        u.context_section_id = 7 AND u.callerid > 0 AND u.active AND c.name='ANSWERED' " + query_x + "\
                    GROUP BY\
                        c.id_sphone, u.name, u.id\
                ) x left join (\
                    SELECT\
                        u.id responsible_user2,\
                        count(b.id) count_briefs,\
                        sum(b4.budget) budget,\
                        sum(case when currency = 'rub' then sum_mediaplan::int4 else 0 end) sum_rub,\
                        sum(case when currency = 'dol' then sum_mediaplan::int4 else 0 end) sum_dol,\
                        sum(case when currency = 'uah' then sum_mediaplan::int4 else 0 end) sum_uah\
                    FROM\
                        res_users u\
                            left join res_groups_users_rel g on (g.uid=u.id)\
                            left join brief_main b on (b.user_id=u.id)\
                            left join brief_part_four b4 on (b.brief_part_four_id=b4.id)\
                    WHERE\
                        u.context_section_id = 7 AND u.callerid > 0 AND u.active AND b.user_id!=b.responsible_user " + query_z + "\
                    GROUP BY\
                        u.callerid, u.name, u.id\
                ) z on (x.responsible_user=z.responsible_user2)\
        ")
        # g.gid IN (47, 49)
        return cr.dictfetchall()

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'crm_lead_atc_report')
        cr.execute("""
            create or replace view crm_lead_atc_report as (
                SELECT
                    row_number() over() as id,
                    x.*,
                    COALESCE(z.responsible_user2, 0) responsible_user2,
                    COALESCE(z.count_briefs, 0) count_briefs,
                    COALESCE(z.budget, 0) budget,
                    COALESCE(z.sum_rub, 0) sum_rub,
                    COALESCE(z.sum_dol, 0) sum_dol,
                    COALESCE(z.sum_uah, 0) sum_uah
                FROM (
                    SELECT
                        u.name name_manager,
                        u.id responsible_user,
                        c.id_sphone callerid,
                        count(c.id) as count_calls,
                        to_char(sum(c.time_of_coll), 'HH24:MI:SS') time_of_coll,
                        to_char(sum(c.time_of_coll) / count(c.id), 'HH24:MI:SS') as call
                    FROM
                        res_users u
                            left join res_groups_users_rel g on (g.uid=u.id)
                            left join crm_phonecall c on (c.id_sphone::int4=u.callerid)
                    WHERE
                        u.context_section_id = 7 AND u.callerid > 0 AND u.active AND c.name='ANSWERED'
                    GROUP BY
                        c.id_sphone, u.name, u.id
                ) x left join (
                    SELECT
                        u.id responsible_user2,
                        count(b.id) count_briefs,
                        sum(b4.budget) budget,
                        sum(case when currency = 'rub' then sum_mediaplan::int4 else 0 end) sum_rub,
                        sum(case when currency = 'dol' then sum_mediaplan::int4 else 0 end) sum_dol,
                        sum(case when currency = 'uah' then sum_mediaplan::int4 else 0 end) sum_uah
                    FROM
                        res_users u
                            left join res_groups_users_rel g on (g.uid=u.id)
                            left join brief_main b on (b.user_id=u.id)
                            left join brief_part_four b4 on (b.brief_part_four_id=b4.id)
                    WHERE
                        u.context_section_id = 7 AND u.callerid > 0 AND u.active AND b.user_id!=b.responsible_user
                    GROUP BY
                        u.callerid, u.name, u.id
                ) z on (x.responsible_user=z.responsible_user2)
            )
        """)

crmLeadATCReport()