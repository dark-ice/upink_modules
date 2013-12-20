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
                  row_number()
                  OVER () AS id,
                  to_char(r.date, 'YYYY-MM-DD') date_end,
                  to_char(r.date, 'YYYY-MM-DD') date_start,
                  extract(WEEK FROM r.date) week_number,

                  r.date date,
                  max(total_fact) total_fact,
                  max(CASE WHEN r.direction = 'PPC' THEN r.plan ELSE 0 END) ppc_plan,
                  max(ppc_fact) ppc_fact,
                  max(ppc_cash) ppc_cash,
                  max(CASE WHEN r.direction = 'SMM' THEN r.plan ELSE 0 END) smm_plan,
                  max(smm_fact) smm_fact,
                  max(smm_cash) smm_cash,
                  max(CASE WHEN r.direction = 'SEO' THEN r.plan ELSE 0 END) seo_plan,
                  max(seo_fact) seo_fact,
                  max(seo_cash) seo_cash,
                  max(CASE WHEN r.direction = 'CALL' THEN r.plan ELSE 0 END) call_plan,
                  max(call_fact) call_fact,
                  max(call_cash) call_cash,
                  max(CASE WHEN r.direction = 'SITE' THEN r.plan ELSE 0 END) web_plan,
                  max(web_fact) web_fact,
                  max(web_cash) web_cash,
                  max(CASE WHEN r.direction = 'VIDEO' THEN r.plan ELSE 0 END) video_plan,
                  max(video_fact) video_fact,
                  max(video_cash) video_cash,
                  max(CASE WHEN r.direction = 'MP' THEN r.plan ELSE 0 END) mp_plan,
                  max(mp_fact) mp_fact,
                  max(mp_cash) mp_cash,
                  max(CASE WHEN r.direction = 'MOSCOW' THEN r.plan ELSE 0 END) moscow_plan,
                  max(moscow_fact) moscow_fact,
                  max(moscow_cash) moscow_cash
                FROM
                    day_report_brief_plan r
                    LEFT JOIN (
                      SELECT
                        h.create_date::DATE date,
                        sum(CASE WHEN bss.direction IN ('PPC', 'SEO', 'SMM', 'CALL', 'SITE', 'VIDEO', 'MP', 'MOSCOW') IS NOT NULL THEN 1 ELSE 0 END) total_fact,
                        sum(CASE WHEN bss.direction = 'PPC' THEN 1 ELSE 0 END) ppc_fact,
                        sum(CASE WHEN bss.direction = 'PPC' THEN b.sum_mediaplan ELSE 0 END) ppc_cash,
                        sum(CASE WHEN bss.direction = 'SMM' THEN 1 ELSE 0 END) smm_fact,
                        sum(CASE WHEN bss.direction = 'SMM' THEN b.sum_mediaplan ELSE 0 END) smm_cash,
                        sum(CASE WHEN bss.direction = 'SEO' THEN 1 ELSE 0 END) seo_fact,
                        sum(CASE WHEN bss.direction = 'SEO' THEN b.sum_mediaplan ELSE 0 END) seo_cash,
                        sum(CASE WHEN bss.direction = 'CALL' THEN 1 ELSE 0 END) call_fact,
                        sum(CASE WHEN bss.direction = 'CALL' THEN b.sum_mediaplan ELSE 0 END) call_cash,
                        sum(CASE WHEN bss.direction = 'SITE' THEN 1 ELSE 0 END) web_fact,
                        sum(CASE WHEN bss.direction = 'SITE' THEN b.sum_mediaplan ELSE 0 END) web_cash,
                        sum(CASE WHEN bss.direction = 'VIDEO' THEN 1 ELSE 0 END) video_fact,
                        sum(CASE WHEN bss.direction = 'VIDEO' THEN b.sum_mediaplan ELSE 0 END) video_cash,
                        sum(CASE WHEN bss.direction = 'MP' THEN 1 ELSE 0 END) mp_fact,
                        sum(CASE WHEN bss.direction = 'MP' THEN b.sum_mediaplan ELSE 0 END) mp_cash,
                        sum(CASE WHEN bss.direction = 'MOSCOW' THEN 1 ELSE 0 END) moscow_fact,
                        sum(CASE WHEN bss.direction = 'MOSCOW' THEN b.sum_mediaplan ELSE 0 END) moscow_cash
                      FROM  (select min(a.create_date) create_date, max(a.brief_id) brief_id, max(a.state_id) state_id from brief_history a WHERE a.state_id= 'media_approval' GROUP BY a.brief_id) h
                      LEFT JOIN brief_main b
                        ON (h.brief_id = b.id)
                      LEFT JOIN brief_services_stage bss
                        ON (bss.id = b.services_ids)
                      WHERE h.state_id = 'media_approval'
                      GROUP BY h.create_date::DATE
                    ) b on (b.date=r.date)
                GROUP BY r.date
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