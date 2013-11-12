# coding=utf-8
__author__ = 'andrey'
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportMP(Model):
    _name = 'day.report.mp'
    _description = u'Ежедневные отчеты - МП'
    _auto = False
    _order = 'date'

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'date': fields.date('Дата'),

        'week_number': fields.integer('Номер недели', group_operator="avg"),

        'ppc_plan': fields.integer('PPC план'),
        'ppc_fact': fields.integer('PPC факт'),
        'ppc_cash': fields.float('PPC $'),

        'web_plan': fields.integer('web план'),
        'web_fact': fields.integer('web факт'),
        'web_cash': fields.float('web $'),
        
        'smm_plan': fields.integer('smm план'),
        'smm_fact': fields.integer('smm факт'),
        'smm_cash': fields.float('smm $'),
        
        'seo_plan': fields.integer('seo план'),
        'seo_fact': fields.integer('seo факт'),
        'seo_cash': fields.float('seo $'),
        
        'call_plan': fields.integer('КЦ план'),
        'call_fact': fields.integer('КЦ факт'),
        'call_cash': fields.float('КЦ $'),
        
        'video_plan': fields.integer('video план'),
        'video_fact': fields.integer('video факт'),
        'video_cash': fields.float('video $'),
        
        'mp_plan': fields.integer('МП план'),
        'mp_fact': fields.integer('МП факт'),
        'mp_cash': fields.float('МП $'),
        
        'moscow_plan': fields.integer('Москва план'),
        'moscow_fact': fields.integer('Москва факт'),
        'moscow_cash': fields.float('Москва $'),

        'total_fact': fields.integer('Зашедшие брифы'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'day_report_mp')
        cr.execute("""
            create or replace view day_report_mp as (
                SELECT
                  row_number() over() as id,
                  to_char(max(r.date), 'YYYY-MM-DD') date_end,
                  to_char(max(r.date), 'YYYY-MM-DD') date_start,
                  extract(week FROM max(r.date)) week_number,

                  max(r.date) date,
                  sum(case when bss.direction in ('PPC', 'SEO', 'SMM', 'CALL', 'SITE', 'VIDEO', 'MP', 'MOSCOW') IS NOT NULL then 1 else 0 end) total_fact,
                  sum(case when bss.direction='PPC' then 1 else 0 end) ppc_fact,
                  sum(case when bss.direction='PPC' then b.sum_mediaplan else 0 end) ppc_cash,
                  sum(case when r.direction='PPC' then r.plan else 0 end) ppc_plan,
                  sum(case when bss.direction='SMM' then 1 else 0 end) smm_fact,
                  sum(case when bss.direction='SMM' then b.sum_mediaplan else 0 end) smm_cash,
                  sum(case when r.direction='SMM' then r.plan else 0 end) smm_plan,
                  sum(case when bss.direction='SEO' then 1 else 0 end) seo_fact,
                  sum(case when bss.direction='SEO' then b.sum_mediaplan else 0 end) seo_cash,
                  sum(case when r.direction='SEO' then r.plan else 0 end) seo_plan,
                  sum(case when bss.direction='CALL' then 1 else 0 end) call_fact,
                  sum(case when bss.direction='CALL' then b.sum_mediaplan else 0 end) call_cash,
                  sum(case when r.direction='CALL' then r.plan else 0 end) call_plan,
                  sum(case when bss.direction='SITE' then 1 else 0 end) web_fact,
                  sum(case when bss.direction='SITE' then b.sum_mediaplan else 0 end) web_cash,
                  sum(case when r.direction='SITE' then r.plan else 0 end) web_plan,
                  sum(case when bss.direction='VIDEO' then 1 else 0 end) video_fact,
                  sum(case when bss.direction='VIDEO' then b.sum_mediaplan else 0 end) video_cash,
                  sum(case when r.direction='VIDEO' then r.plan else 0 end) video_plan,
                  sum(case when bss.direction='MP' then 1 else 0 end) mp_fact,
                  sum(case when bss.direction='MP' then b.sum_mediaplan else 0 end) mp_cash,
                  sum(case when r.direction='MP' then r.plan else 0 end) mp_plan,
                  sum(case when bss.direction='MOSCOW' then 1 else 0 end) moscow_fact,
                  sum(case when bss.direction='MOSCOW' then b.sum_mediaplan else 0 end) moscow_cash,
                  sum(case when r.direction='MOSCOW' then r.plan else 0 end) moscow_plan

                FROM
                  day_report_brief_plan r
                  LEFT JOIN brief_history h on (h.cr_date::date=r.date AND h.state_id='media_approval')
                  LEFT JOIN brief_main b on (h.brief_id=b.id)
                  LEFT JOIN brief_services_stage bss on (bss.id=b.services_ids)
                GROUP BY r.date::date
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

        return super(ReportMP, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)
ReportMP()