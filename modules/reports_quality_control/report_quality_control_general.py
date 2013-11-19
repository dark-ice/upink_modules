# coding=utf-8
import calendar
import numpy
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportQualityControlGeneral(Model):
    _name = 'report.quality.control.general'
    _auto = False

    def _get_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['quality_ids', 'partner_id'], context):
            ydolit = self.pool.get('res.partner.quality.control')._get_ydolit(cr, uid, tuple(set(record['quality_ids'])), '', {},
                                                                              context=None)
            points = []
            indexes = []

            for k, val in ydolit.iteritems():
                points.append(val['level_ydolit'])
                indexes.append(val['index_ydolit'])

            money_sum = self.pool.get('res.partner')._get_report_payment(cr, uid, [record['partner_id'][0],], name, arg, context=None)

            res[record['id']] = {
                'quality_point': numpy.mean(points),
                'quality_index': numpy.mean(indexes),
                'payment_sum': money_sum[record['partner_id'][0]][0][2]['payment_sum']
            }
        return res

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнеры'),
        'direction': fields.char('Услуга', size=128),
        'specialist': fields.many2one('res.users', 'Менеджеры'),
        'manager_id': fields.many2one('res.users', 'Аккаует-Менеджер'),
        'terms_of_service': fields.float('Срок предоставления услуги'),
        'terms_of_service_anket': fields.char('Анкета', size=128),
        'conformity': fields.float('Соответствие услуги всем входным требованиям'),
        'conformity_anket': fields.char('Анкета', size=128),
        'quality_feedback': fields.float('Скорость и полнота ответов менеджера'),
        'quality_feedback_anket': fields.char('Анкета', size=128),
        'completeness_of_reporting': fields.float('Полнота отчетов и соболюдение сроков их предоставления'),
        'completeness_of_reporting_anket': fields.char('Анкета', size=128),
        'comment': fields.char('Комментарий', size=512),
        'quality_point': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Уровень удовлетворенности по анкетк %',
        ),
        'mbo': fields.float('MBO по услуге %'),
        'quality_index': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Индекс удов',
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
                    CASE WHEN ppc.specialist_id IS NOT null THEN ppc.specialist_id
                    ELSE
                      CASE WHEN site.specialist_id IS NOT null THEN site.specialist_id
                      ELSE
                        CASE WHEN smm.specialist_id IS NOT null THEN smm.specialist_id
                        ELSE
                          CASE WHEN seo.specialist_id IS NOT null THEN seo.specialist_id END END END END specialist,

                  CASE WHEN crit.name = 'terms_of_service' THEN crit.value END terms_of_service,
                  CASE WHEN crit.name = 'conformity' THEN crit.value END conformity,
                  CASE WHEN crit.name = 'quality_feedback' THEN crit.value END quality_feedback,
                  CASE WHEN crit.name = 'completeness_of_reporting' THEN crit.value END completeness_of_reporting,
                  case when th.name is null then p.user_id else th.name end manager_id,
                  bss.direction,
                  pl.partner_id,
                  rpqc.mbo,
                  irp.payment_sum,
                  array_agg(rpqc.id) quality_ids,
                  k.name period_name,
                  k.id period_id,
                  p.terms_of_service terms_of_service_anket,
                  p.conformity conformity_anket,
                  p.quality_feedback quality_feedback_anket,
                  p.completeness_of_reporting completeness_of_reporting_anket,
                  crit.comment
                FROM res_partner_quality_control AS rpqc
                JOIN res_partner_quality_criteria as crit
                  ON (crit.quality_id = rpqc.id)
                JOIN process_launch pl
                  ON (rpqc.partner_id = pl.partner_id AND rpqc.service_id = pl.service_id)
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
                  ON (irp.partner_id = p.id AND irp.period_id = rpqc.period_id)
                GROUP BY
                  pl.partner_id,
                  rpqc.id,
                  quality_id,
                  manager_id,
                  ppc.specialist_id,
                  site.specialist_id,
                  smm.specialist_id,
                  seo.specialist_id,
                  bss.direction,
                  k.name,
                  k.id,
                  th.name,
                  p.user_id,
                  p.terms_of_service,
                  p.conformity,
                  p.quality_feedback,
                  p.completeness_of_reporting,
                  crit.comment,
                  crit.value,
                  crit.name,
                  irp.payment_sum
            )
        """)

ReportQualityControlGeneral()