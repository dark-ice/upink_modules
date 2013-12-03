# coding=utf-8
import calendar
import numpy
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportQualityControlGeneral(Model):
    _name = 'report.quality.control.general'
    _auto = False
    _order = 'period_id DESC'

    def _get_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['quality_ids', 'partner_id', 'period_id'], context):
            ydolit = self.pool.get('res.partner.quality.control')._get_ydolit(cr, uid, tuple(set(record['quality_ids'])), '', {},
                                                                              context=None)
            points = []
            indexes = []
            mbo = []

            for k, val in ydolit.iteritems():
                points.append(val['level_ydolit'])
                indexes.append(val['index_ydolit'])
                mbo.append(val['mbo'])

            money_sum = self.pool.get('res.partner')._get_report_payment(cr, uid, [record['partner_id'][0],], name, arg, context=None)
            sum = 0.0
            for rec in money_sum[record['partner_id'][0]]:
                record['period_id'][0]
                if rec[2]['period_id'] == record['period_id'][0]:
                    sum = rec[2]['payment_sum']

            res[record['id']] = {
                'quality_point': numpy.mean(points),
                'quality_index': numpy.mean(indexes),
                'mbo': numpy.mean(mbo),
                'payment_sum': sum
            }
        return res

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'direction': fields.char('Направление', size=128),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'specialist_id': fields.many2one('res.users', 'Аккаунт-Менеджер'),
        'manager_id': fields.many2one('res.users', 'Менеджер'),
        'terms_of_service': fields.float('Срок предоставления услуги'),
        'terms_of_service_anket': fields.char('Анкета', size=128),
        'conformity': fields.float('Соответствие услуги всем входным требованиям'),
        'conformity_anket': fields.char('Анкета', size=128),
        'quality_feedback': fields.float('Скорость и полнота ответов менеджера'),
        'quality_feedback_anket': fields.char('Анкета', size=128),
        'completeness_of_reporting': fields.float('Полнота отчетов и соблюдение сроков их предоставления'),
        'completeness_of_reporting_anket': fields.char('Анкета', size=128),
        'comentariy': fields.text('Комментарий', size=1024),
        'quality_point': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Уровень удовл. по анкете %',
        ),
        'mbo': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='MBO по услуге, %',
        ),
        'quality_index': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Индекс удовл.',
        ),
        'period_name': fields.char('Период', size=10),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'quality_ids': fields.char('id оценки услуги', size=256),
        'payment_sum': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Бюджет',
        ),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_quality_control_general')
        cr.execute("""
            create or replace view report_quality_control_general as (
                SELECT
                  row_number() over() as id,
                  r.specialist_id,
                  r.manager_id,
                  r.period_id,
                  r.period_name,
                  r.service_id,
                  max(r.direction) direction,
                  r.partner_id,
                  r.process_id,
                  max(r.terms_of_service) terms_of_service,
                  max(r.conformity) conformity,
                  max(r.quality_feedback) quality_feedback,
                  max(r.completeness_of_reporting) completeness_of_reporting,
                  max(r.terms_of_service_anket) terms_of_service_anket,
                  max(r.conformity_anket) conformity_anket,
                  max(r.quality_feedback_anket) quality_feedback_anket,
                  max(r.completeness_of_reporting_anket) completeness_of_reporting_anket,
                  array_to_string(array_agg(CAST(r.comment AS text)),',') as comentariy,
                  array_agg(r.quality_id) quality_ids
                FROM (
                SELECT
                    CASE WHEN ppc.specialist_id IS NOT null THEN ppc.specialist_id
                    ELSE
                      CASE WHEN site.specialist_id IS NOT null THEN site.specialist_id
                      ELSE
                        CASE WHEN smm.specialist_id IS NOT null THEN smm.specialist_id
                        ELSE
                          CASE WHEN seo.specialist_id IS NOT null THEN seo.specialist_id END END END END specialist_id,

                  CASE WHEN crit.name = 'terms_of_service' THEN crit.value END terms_of_service,
                  CASE WHEN crit.name = 'conformity' THEN crit.value END conformity,
                  CASE WHEN crit.name = 'quality_feedback' THEN crit.value END quality_feedback,
                  CASE WHEN crit.name = 'completeness_of_reporting' THEN crit.value END completeness_of_reporting,
                  case when th.name is null then p.user_id else th.name end manager_id,
                  bss.direction,
                  rpqc.service_id,
                  pl.partner_id,
                  pl.process_id,
                  rpqc.id quality_id,
                  k.name period_name,
                  k.id period_id,
                  p.terms_of_service terms_of_service_anket,
                  p.conformity conformity_anket,
                  p.quality_feedback quality_feedback_anket,
                  p.completeness_of_reporting completeness_of_reporting_anket,
                  CASE WHEN crit.comment is not NULL THEN crit.comment END as comment
                FROM res_partner_quality_control AS rpqc
                LEFT JOIN res_partner_quality_criteria as crit
                  ON (crit.quality_id = rpqc.id)
                JOIN process_launch pl
                  ON (rpqc.partner_id = pl.partner_id AND rpqc.service_id = pl.service_id AND state='in_process')
                LEFT JOIN res_partner p
                  ON (p.id=rpqc.partner_id)
                JOIN brief_services_stage as bss
                  ON (bss.id = pl.service_id)
                LEFT JOIN process_ppc ppc
                  ON (pl.id = ppc.launch_id)
                LEFT JOIN process_site site
                  ON (pl.id = site.launch_id)
                LEFT JOIN process_seo seo
                  ON (pl.id = seo.launch_id)
                LEFT JOIN process_smm smm
                  ON (pl.id = smm.launch_id)
                JOIN kpi_period k
                  ON (k.id = rpqc.period_id)
                LEFT JOIN transfer_history AS th
                  ON (th.partner_id = rpqc.partner_id AND (k.name>=to_char(th.create_date, 'YYYY/MM')) AND k.name<(SELECT to_char(th2.create_date, 'YYYY/MM') FROM transfer_history th2 WHERE th2.partner_id = rpqc.partner_id AND th2.create_date > th.create_date LIMIT 1))
                LEFT JOIN res_users u on (u.id=th.name)
                LEFT JOIN invoice_reporting_period irp
                  ON (irp.partner_id = p.id AND irp.period_id = rpqc.period_id)) r
GROUP BY
  r.service_id,
  r.partner_id,
  r.period_id, r.period_name,
  r.specialist_id,
  r.manager_id,
  r.process_id
            )
        """)

ReportQualityControlGeneral()