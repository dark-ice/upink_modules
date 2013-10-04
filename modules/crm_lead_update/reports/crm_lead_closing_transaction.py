# -*- coding: utf-8 -*-
import tools
from osv import fields, osv

NOT_OPERATOR = '!'
OR_OPERATOR = '|'
AND_OPERATOR = '&'


class crmLeadClosingTransactionReport(osv.osv):
    _name = "crm.lead.closing.transaction.report"
    _description = u"Закрытие сделок"
    _auto = False
    _rec_name = 'user_id'

    def _get_service(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if ids:
            for data in self.browse(cr, uid, ids, context):
                service = str()
                if data.ppc_service_id:
                    service = "PPC: %s" % data.ppc_service_id.name
                if data.seo_promotion_word:
                    service = "SEO: Продвижение по словам"
                if data.seo_promotion_trafic:
                    service = "SEO: Продвижение по трафику"
                if data.seo_audit:
                    service = "SEO: SEO аудит"
                if data.seo_optim:
                    service = "SEO: SEO оптимизация"
                if data.seo_promotion_other:
                    service = "SEO: Другой вариант"
                if data.smm_targeted_advertising:
                    service = "SMM: Таргетированная реклама"
                if data.smm_contest:
                    service = "SMM: Конкурс"
                if data.smm_lead_management:
                    service = "SMM: Лид менеджмент"
                if data.smm_hidden_marketing:
                    service = "SMM: Скрытый маркетинг"
                if data.smm_reputation_management:
                    service = "SMM: Управление репутацией"
                if data.inc_sum:
                    service = "Аутсорсинговый контакт-центр: Входящая кампания"
                if data.outc_sum:
                    service = "Аутсорсинговый контакт-центр: Исходящая кампания"

                res[data.id] = service
        return res

    _columns = {
        'date_start': fields.date('Период', select=True),
        'date_end': fields.date('Период', select=True),
        'date': fields.date('Date Order', select=True),

        'partner_id': fields.many2one('res.partner', 'Партнер', readonly=True),
        'user_id': fields.many2one('res.users', 'Менеджер продаж', readonly=True, domain="[('groups_id','in',[48, 50])]"),
        'responsible_id': fields.many2one('res.users', 'Менеджер по привлечению', readonly=True),
        'manager_upwork_id': fields.many2one('res.users', 'Менеджер по развитию', readonly=True),

        'count_cancel': fields.integer('Исклчая отказ', readonly=True),
        'count_talks': fields.integer('Переговоры', readonly=True),
        'count_approval': fields.integer('Утверждение договора', readonly=True),
        'count_done': fields.integer('Счет оплачен', readonly=True),
        'count_dangling': fields.integer('Зависшие переговоры', readonly=True),


        'ppc_sum': fields.float('Сумма по ppc', readonly=True),
        'ppc_paydate': fields.datetime('Дата оплаты', readonly=True, select=True),
        'seo_sum': fields.float('Сумма по seo', readonly=True),
        'seo_paydate': fields.datetime('Дата оплаты', readonly=True, select=True),
        'smm_sum': fields.float('Сумма по smm', readonly=True),
        'smm_paydate': fields.datetime('Дата оплаты', readonly=True, select=True),
        'outc_sum': fields.float('Сумма по outc', readonly=True),
        'outc_paydate': fields.datetime('Дата оплаты', readonly=True, select=True),
        'inc_sum': fields.float('Сумма по inc', readonly=True),
        'inc_paydate': fields.datetime('Дата оплаты', readonly=True, select=True),
        'total_sum': fields.float('Общаяя сумма', readonly=True),

        'ppc_service_id': fields.many2one('ppc.reklam.stage', 'Рекламная система', readonly=True),
        'seo_promotion_word': fields.boolean('Продвижение по словам'),
        'seo_promotion_trafic': fields.boolean('Продвижение по трафику'),
        'seo_audit': fields.boolean('SEO аудит'),
        'seo_optim': fields.boolean('SEO оптимизация'),
        'seo_promotion_other': fields.boolean('Другой вариант'),
        'smm_targeted_advertising': fields.boolean('Таргетированная реклама'),
        'smm_contest': fields.boolean('Конкурс'),
        'smm_lead_management': fields.boolean('Лид менеджмент'),
        'smm_hidden_marketing': fields.boolean('Скрытый маркетинг'),
        'smm_reputation_management': fields.boolean('Управление репутацией'),

        'service': fields.function(_get_service,
                                   method=True,
                                   string="Услуга",
                                   type="char"),

    }

    _order = 'user_id desc, partner_id'

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        user_id = [item for item in domain if item[0] == 'user_id']
        date_start = [item for item in domain if item[0] == 'date_start']
        date_end = [item for item in domain if item[0] == 'date_end']

        new_domain = []
        if user_id:
            new_domain.append(user_id[0])

        count_or = 0
        tmp_domain = []
        processes = ('date', 'ppc_paydate', 'seo_paydate', 'smm_paydate', 'outc_paydate', 'inc_paydate')

        if date_end and date_start:
            for process in processes:
                tmp_domain += ['&', (process, '<=', date_end[0][2]), (process, '>=', date_start[0][2])]
                count_or = 5
        else:
            if date_start and not date_end:
                date = date_start[0][2]
                tmp_domain += [(process, '>=', date) for process in processes]
                count_or += 5
            if date_end and not date_start:
                date = date_end[0][2]
                tmp_domain += [(process, '<=', date) for process in processes]
                if count_or == 5:
                    count_or += 6
                else:
                    count_or += 5
        ors = ['|'] * count_or
        if count_or:
            new_domain += ors + tmp_domain
        return super(crmLeadClosingTransactionReport, self).read_group(cr, uid, new_domain, fields, groupby, offset, limit, context, orderby)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'crm_lead_closing_transaction_report')
        cr.execute("""
            create or replace view crm_lead_closing_transaction_report as (
                SELECT
                    row_number() over() as id,
                    l.user_id user_id,
                    l.create_date date,
                    to_char(max(l.create_date), 'YYYY-MM-DD') date_end,
                    to_char(min(l.create_date), 'YYYY-MM-DD') date_start,
                    sum(case when l.stage_id != 41 then 1 else 0 end) count_cancel,
                    sum(case when l.stage_id = 36 then 1 else 0 end) count_talks,
                    sum(case when l.stage_id = 53 then 1 else 0 end) count_dangling,
                    sum(case when l.stage_id = 37 then 1 else 0 end) count_approval,
                    sum(case when l.stage_id = 39 then 1 else 0 end) count_done,
                    max(l.partner_id) partner_id,
                    max(l.responsible_user) responsible_id,
                    max(p.user_id) manager_upwork_id,

                    ppc_stage.summ_pay_$ ppc_sum,
                    ppc_stage.pay_detetime ppc_paydate,
                    max(ppc.reklam_id) ppc_service_id,

                    seo_stage.sum_fackt seo_sum,
                    seo_stage.pay_date_fackt seo_paydate,
                    seo.promotion_word seo_promotion_word,
                    seo.promotion_trafic seo_promotion_trafic,
                    seo.seo_audit seo_audit,
                    seo.seo_optim seo_optim,
                    seo.promotion_other seo_promotion_other,

                    smm_stage.sum smm_sum,
                    smm_stage.pay_date smm_paydate,
                    smm.targeted_advertising smm_targeted_advertising,
                    smm.contest smm_contest,
                    smm.lead_management smm_lead_management,
                    smm.hidden_marketing smm_hidden_marketing,
                    smm.reputation_management smm_reputation_management,

                    outc.pay_sum outc_sum,
                    outc.pay_day outc_paydate,
                    inc.pay_sum inc_sum,
                    inc.pay_day inc_paydate,

                    (COALESCE(max(ppc_stage.summ_pay_$),0)+COALESCE(max(seo_stage.sum_fackt),0)+COALESCE(max(smm_stage.sum),0)+COALESCE(max(outc.pay_sum),0)+COALESCE(max(inc.pay_sum),0)) total_sum

                FROM
                    crm_lead l
                        left join ppc_company ppc on (l.partner_id=ppc.partner_id)
                        left join ppc_payments_stage ppc_stage on (ppc_stage.ppc_company_id=ppc.id)
                        left join seo_strategys seo on (l.partner_id=seo.partner_id)
                        left join seo_strategys_payments_stage seo_stage on (seo_stage.seo_strategys_id=seo.id)
                        left join smm_strategy smm on (l.partner_id=smm.partner_id)
                        left join smm_strategy_payments smm_stage on (smm_stage.smm_strategy_id=smm.id)
                        left join out_campaign outc on (l.partner_id=outc.partner_id)
                        left join in_campaign inc on (l.partner_id=inc.partner_id)
                        left join video v on (l.partner_id=v.partner_id)
                        left join res_partner p on (l.partner_id=p.id)
                        left join res_users u on (l.user_id=u.id)
                        left join res_groups_users_rel g on (g.uid=u.id)
                WHERE
                    u.company_id = 4 AND u.active = True AND (l.company_type = 'upsale' OR l.company_type IS Null) AND g.gid IN (48, 50)
                GROUP BY
                    l.user_id,
                    l.partner_id,
                    ppc_stage.summ_pay_$,
                    ppc_stage.pay_detetime,
                    seo_stage.sum_fackt,
                    seo_stage.pay_date_fackt,
                    smm_stage.sum,
                    smm_stage.pay_date,
                    outc.pay_sum,
                    outc.pay_day,
                    inc.pay_sum,
                    inc.pay_day,
                    smm.targeted_advertising,
                    smm.contest,
                    smm.lead_management,
                    smm.hidden_marketing,
                    smm.reputation_management,
                    seo.promotion_word,
                    seo.promotion_trafic,
                    seo.seo_audit,
                    seo.seo_optim,
                    seo.promotion_other,
                    l.create_date
            )
        """)

crmLeadClosingTransactionReport()