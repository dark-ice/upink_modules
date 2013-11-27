# -*- coding: utf-8 -*-
from datetime import date
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model
from reports_day_direction.yandex_direct import YandexDirect


class ReportDayPPCStatistic(Model):
    _name = 'report.day.ppc.statistic'
    _description = u'Ежедневный отчет направлений - PPC - значения статистики'
    _order = 'date DESC'

    _columns = {
        'name': fields.selection(
            (('direct', 'Яндекс.Директ'), ('adwords', 'Google.Adwords')),
            'Рекламная система'
        ),
        'date': fields.date('Дата'),
        'cash': fields.float('Сумма'),
        'campaign': fields.char('ID кампании', size=100),
        'ppc_id': fields.many2one('process.ppc', 'Проект'),
        'specialist_id': fields.related(
            'ppc_id',
            'specialist_id',
            type='many2one',
            relation='res.users',
            string='Аккаунт-менеджер')
    }

    _defaults = {
        'campaign': lambda s, c, u, cntx: cntx.get('campaign'),
    }

    def onchange_ppc(self, cr, uid, ids, ppc_id='', campaign='', context=None):
        specialist_id = False
        if campaign:
            ppc_ids = self.pool.get('process.ppc').search(cr, 1, [('campaign', '=', campaign)])
            if ppc_ids:
                ppc_id = ppc_ids[0]
            else:
                ppc_id = False
        if ppc_id:
            ppc = self.pool.get('process.ppc').read(cr, 1, ppc_id, ['campaign', 'specialist_id'])
            campaign = ppc['campaign']
            specialist_id = ppc['specialist_id'][0]
        return {'value': {'campaign': campaign, 'ppc_id': ppc_id, 'specialist_id': specialist_id}}

    def update(self, cr, uid):
        yandex_campaign = []
        date_start = date_end = date.today().strftime("%Y-%m-%d")
        ppc_dict = {}
        ppc_pool = self.pool.get('process.ppc')
        ppc_ids = ppc_pool.search(cr, 1, [])
        records = ppc_pool.read(cr, 1, ppc_ids, ['campaign', 'advertising_id', 'partner_id', 'specialist_id', 'domain_zone', 'date_start'])
        for record in records:
            if date_start > record['date_start'] and record['date_start']:
                date_start = record['date_start']
            if record['advertising_id'] and record['advertising_id'][0] == 1 and record['campaign']:
                yandex_campaign.append(int(record['campaign']))
                ppc_dict[int(record['campaign'])] = record['id']

        yandex = YandexDirect()
        if yandex_campaign:
            if len(yandex_campaign) <= 100:
                yandex_result = yandex.get_summary_stat(yandex_campaign, date_start, date_end)
            else:
                yandex_result = {}
                count = len(yandex_campaign) // 100 + 1
                for line in range(count):
                    yandex_result.update(
                        yandex.get_summary_stat(yandex_campaign[line*100:(line+1)*100], date_start, date_end)
                    )

            for item in yandex_result:

                if not self.search(cr, 1, [('campaign', '=', item['CampaignID']), ('date', '=', item['StatDate'])]):
                    self.create(
                        cr,
                        1,
                        {
                            'campaign': item['CampaignID'],
                            'date': item['StatDate'],
                            'cash': item['SumSearch'],
                            'name': 'direct',
                            'ppc_id': ppc_dict[item['CampaignID']]
                        })
        return True


ReportDayPPCStatistic()


class ReportDayPPC(Model):
    _name = 'report.day.ppc'
    _description = u'Ежедневный отчет направлений - PPC'
    _auto = False
    _order = 'date DESC'

    _columns = {
        'date_start': fields.date('Дата начала'),
        'date_end': fields.date('Дата конца'),

        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'specialist_id': fields.many2one('res.users', 'Аккаунт-менеджер'),
        'domain_zone': fields.selection((('ru', 'ru'), ('ua', 'ua')), 'Доменная зона'),
        'campaign': fields.char('ID кампании', size=200),
        'cash': fields.float('Сумма'),
        'date': fields.date('Дата'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_day_ppc')
        cr.execute("""
            create or replace view report_day_ppc as (
                SELECT
                  row_number() over() as id,
                  s.date date_end,
                  s.date date_start,
                  l.partner_id,
                  l.service_id,
                  p.specialist_id,
                  p.domain_zone,
                  p.campaign,
                  s.cash,
                  s.date
                FROM
                  process_ppc p
                  LEFT JOIN process_launch l on (l.id=p.launch_id)
                  LEFT JOIN report_day_ppc_statistic s on (p.campaign=s.campaign)
                WHERE p.state='implementation' and p.campaign is not null
            )""")

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        for item in args:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
        return super(ReportDayPPC, self).search(cr, user, args, offset, limit, order, context, count)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for item in domain:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='

        return super(ReportDayPPC, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)

ReportDayPPC()



