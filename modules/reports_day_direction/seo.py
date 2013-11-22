# -*- coding: utf-8 -*-
from datetime import date
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model
from reports_day_direction.allpositions import proxy


class ReportDaySEOStatistic(Model):
    _name = 'report.day.seo.statistic'
    _description = u'Ежедневный отчет направлений - SEO - значения статистики'
    _order = 'date DESC'
    
    _columns = {
        'date': fields.date('Дата'),
        'fact': fields.float('Факт'),
        'top3': fields.float('ТОП 3'),
        'top10': fields.float('ТОП 10'),
        'campaign': fields.char('ID кампании', size=100),
        'seo_id': fields.many2one('process.seo', 'SEO'),
        'process_type': fields.selection(
            (
                ('top', 'Продвижение в топ'),
                ('traffic', 'Трафик'),
                ('optim', 'Внутрення оптимизация'),
                ('support', 'Поддержка'),
            ), 'Тип проекта'),
    }

    _defaults = {
        'campaign': lambda s, c, u, cntx: cntx.get('campaign'),
    }

    def onchange_seo(self, cr, uid, ids, seo_id='', campaign='', context=None):
        if seo_id:
            seo = self.pool.get('process.seo').read(cr, 1, seo_id, ['campaign'])
            campaign = seo['campaign']
        elif not seo_id and campaign:
            seo_ids = self.pool.get('process.seo').search(cr, 1, [('campaign', '=', campaign)])
            if seo_ids:
                seo_id = seo_ids[0]
            else:
                seo_id = False
        return {'value': {'campaign': campaign, 'seo_id': seo_id}}
    
    def update(self, cr, uid):
        seo_ids = self.pool.get('process.seo').search(cr, 1, [('campaign', '!=', False)])
        for record in self.pool.get('process.seo').read(cr, 1, seo_ids, ['campaign', 'process_type']):
            dates = proxy.get_report_dates(int(record['campaign']))
            for report_date in dates.values():
                if not self.search(cr, 1, [('campaign', '=', record['campaign']), ('date', '=', report_date)]):
                    report = proxy.get_report(int(record['campaign']), report_date)
                    self.create(
                        cr,
                        1,
                        {
                            'campaign': record['campaign'],
                            'date': report_date,
                            'top3': report['top3'],
                            'top10': report['top10'],
                            'process_type': record['process_type'],
                            'seo_id': record['id'],
                        })
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
        'fact': fields.float('Сумма'),
        'top3': fields.float('Топ 3'),
        'top10': fields.float('Топ 10'),
        'date': fields.date('Дата'),
        'process_type': fields.selection(
            (
                ('top', 'Продвижение в топ'),
                ('traffic', 'Трафик'),
                ('optim', 'Внутрення оптимизация'),
                ('support', 'Поддержка'),
            ), 'Тип проекта'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_day_seo')
        cr.execute("""
            create or replace view report_day_seo as (
                SELECT
                  row_number() over() as id,
                  p.date_start,
                  p.date_start date_end,
                  l.partner_id,
                  l.service_id,
                  p.specialist_id,
                  p.process_type,
                  p.campaign,
                  s.top3,
                  s.top10,
                  s.fact,
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