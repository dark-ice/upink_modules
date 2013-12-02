# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportDaySite(Model):
    _name = "report.day.site"
    _description = "Отчет по сайтам"
    _auto = False
    _columns = {
        'partner_id': fields.many2one('res.partner', "Проект"),
        'stage': fields.char('этап', size=128),
        'now_stage': fields.char('Текущий этап', size=128),
        'now_plan_fn': fields.date('Планируемая дата завершения текущего этапа'),
        'plan_date_st': fields.date('Планируемая дата начала'),
        'plan_date_fn': fields.date('Планируемая дата окончания'),
        'real_date_st': fields.date('Фактическая дата начала'),
        'real_date_fn': fields.date('Фактическая дата окончания'),
        'date_end': fields.date('Production'),
    }
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_day_site')
        cr.execute("""
            create or replace view report_day_site as (
                SELECT
                    row_number() over() as id,
                      pl.partner_id,
                      pss.stage,
                      pss.plan_date_st,
                      pss.plan_date_fn,
                      pss.real_date_st,
                      pss.real_date_fn,
                      ps.date_end,

                      asd.plan_date_fn as now_plan_fn,
                      asd.stage as now_stage

                    from process_site ps
                    join process_launch pl
                      on (pl.id = ps.launch_id)
                    join process_site_stage pss
                      on (pss.site_id = ps.id)
                    left join (
                    SELECT
                      s.id,
                      ss.plan_date_fn,
                      ss.stage
                    FROM process_site s
                      LEFT JOIN process_site_stage ss on (ss.site_id=s.id)
                    WHERE ss.real_date_fn is NULL AND real_date_st is not null) asd on (asd.id=ps.id)
                    where ps.state = 'work' and pss.plan_date_fn is not NULL and pss.plan_date_st is not NULL and pss.real_date_st is not NULL
            )""")

ReportDaySite()