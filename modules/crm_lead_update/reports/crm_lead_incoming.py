# -*- coding: utf-8 -*-
import tools
from osv import fields, osv


class crmLeadIncomingReport(osv.osv):
    _name = "crm.lead.incoming.report"
    _description = u"Входящие заявки"
    _auto = False
    _rec_name = 'user_id'

    _columns = {
        'date_start': fields.date('Период', select=True),
        'date_end': fields.date('Период', select=True),
        'date': fields.date('Date Order', select=True),

        'user_id': fields.many2one('res.users', 'Менеджер продаж', readonly=True, domain="[('id', 'in', (98, 259, 457, 523))]"),
        'service_id': fields.many2one('brief.services.stage', 'Наименование услуги', readonly=True),
        'budget': fields.integer("Бюджет", readonly=True),
        'source': fields.many2one('crm.source.stage', 'Источник', readonly=True),
        'categ_id': fields.many2one('crm.case.categ', 'Категория', readonly=True),
        'site': fields.char("Основной сайт", size=256, readonly=True),
        'last_call': fields.datetime('Последний звонок', select=True),
        'stage_id': fields.many2one('crm.case.stage', 'Этапы'),
        'sum_rub': fields.float("Сумма медиапалнов руб", readonly=True),
        'sum_dol': fields.float("Сумма медиапалнов $", readonly=True),
        'sum_uah': fields.float("Сумма медиапалнов грн", readonly=True),

    }

    _order = 'user_id desc, site'

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        user_id = [item for item in domain if item[0] == 'user_id']
        site = [item for item in domain if item[0] == 'site']
        date_start = [item for item in domain if item[0] == 'date_start']
        date_end = [item for item in domain if item[0] == 'date_end']

        new_domain = []
        if user_id:
            new_domain.append(user_id[0])
        if site:
            new_domain.append(site[0])

        if date_start:
            date_s = ('date', '>=', date_start[0][2])
            new_domain.append(date_s)

        if date_end:
            date_e = ('date', '<=', date_end[0][2])
            new_domain.append(date_e)

        return super(crmLeadIncomingReport, self).read_group(cr, uid, new_domain, fields, groupby, offset, limit, context, orderby)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'crm_lead_incoming_report')
        cr.execute("""
            create or replace view crm_lead_incoming_report as (
                SELECT
                     row_number() over() as id,
                     l.user_id user_id,
                     b.create_date date,
                     to_char(max(l.create_date), 'YYYY-MM-DD') date_end,
                     to_char(min(l.create_date), 'YYYY-MM-DD') date_start,
                     l.source source,
                     l.categ_id categ_id,
                     l.name site,
                     b.services_ids service_id,
                     sum(case when b.currency = 'rub' then cast(b.sum_mediaplan as double precision) else 0 end) sum_rub,
                     sum(case when b.currency = 'dol' then cast(b.sum_mediaplan as double precision) else 0 end) sum_dol,
                     sum(case when b.currency = 'uah' then cast(b.sum_mediaplan as double precision) else 0 end) sum_uah,
                     b4.budget budget,
                     max(c.date) last_call,
                     l.stage_id stage_id
                FROM
                     res_partner l
                         left join brief_main b on (b.partner_id=l.id)
                         left join brief_part_four b4 on (b.brief_part_four_id=b4.id)
                         left join res_users u on (l.user_id=u.id)
                         left join crm_phonecall c on (c.opportunity_id=l.id)
                WHERE
                     u.company_id = 4 AND u.active = True AND l.lead=True
                     AND b.id > 0 AND u.id IN (98, 259, 457, 523)
                GROUP BY
                     l.name,
                     l.user_id,
                     b.create_date,
                     l.source,
                     l.categ_id,
                     b.services_ids,
                     b4.budget,
                     l.stage_id
            )
        """)

crmLeadIncomingReport()