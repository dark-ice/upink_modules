# -*- coding: utf-8 -*-
from datetime import date
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportDaySEOStatistic(Model):
    _name = 'report.day.seo.statistic'
    _description = u'Ежедневный отчет направлений - SEO - значения статистики'
    _order = 'date DESC'
    
    _columns = {
        'date': fields.date('Дата'),
        'cash': fields.float('Сумма'),
        'campaign': fields.char('ID кампании', size=100)
    }
    
    def update(self, cr, uid):
        return True
ReportDaySEOStatistic()


class ReportDaySEO(Model):
    _name = 'report.day.seo'
    _description = u'Ежедневный отчет направлений - SEO'
    _auto = False

    _columns = {
        'date_start': fields.date('Дата начала'),
        'date_end': fields.date('Дата конца'),

        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'specialist_id': fields.many2one('res.users', 'Специалист'),
        'campaign': fields.char('ID кампании', size=200),
        'cash': fields.float('Сумма'),
        'date': fields.date('Дата'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_day_seo')
        cr.execute("""
            create or replace view report_day_seo as (
                SELECT
                  row_number() over() as id,
                  p.date_end,
                  p.date_start,
                  l.partner_id,
                  l.service_id,
                  p.specialist_id,
                  p.campaign,
                  s.cash,
                  s.date
                FROM
                  process_seo p
                  LEFT JOIN process_launch l on (l.id=p.launch_id)
                  LEFT JOIN report_day_seo_statistic s on (p.campaign=s.campaign)
                WHERE p.state='implementation'
            )""")

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if isinstance(args, tuple):
            args = list(args)
        for item in args:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
        return super(ReportDaySEO, self).search(cr, user, args, offset, limit, order, context, count)

ReportDaySEO()