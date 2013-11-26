# coding=utf-8
import calendar
import numpy
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportQualityControlSpecialist(Model):
    _name = 'report.quality.control.specialist'
    _order = 'period_name, specialist'
    _auto = False

    def _get_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['quality_id'], context):

            ydolit = self.pool.get('res.partner.quality.control')._get_ydolit(cr, uid, record['quality_id'], '', {}, context=None)
            points = []
            indexes = []
            mbo = []
            for k, val in ydolit.iteritems():
                points.append(val['level_ydolit'])
                indexes.append(val['index_ydolit'])
                mbo.append(val['mbo'])

            res[record['id']] = {
                'quality_point': numpy.mean(points),
                'quality_index': numpy.mean(indexes),
                'partner_cnt': len(record['quality_id']),
                'mbo': numpy.mean(mbo),
            }
        return res

    _columns = {
        'specialist': fields.many2one('res.users', 'Специалист'),
        'quality_point': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Уровень удовлетворенности',
            group_operator='avg'
        ),
        'quality_index': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Индекс удовлетворенности',
            group_operator='avg'
        ),
        'partner_cnt': fields.function(
            _get_date,
            type='integer',
            multi='need_date',
            string='Количество партнеров',
        ),
        'mbo': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='MBO по услуге',
            group_operator='avg'
        ),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'period_name': fields.char('Период', size=10),
        #'partner_id': fields.many2one('res.partner', 'Партнер'),
        'quality_id': fields.char('массив', size=256),
        #'process_id': fields.integer('процесс'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_quality_control_specialist')
        cr.execute("""
            create or replace view report_quality_control_specialist as (
                SELECT
                  row_number() over() as id,
                  r.specialist,
                  r.period_name,
                  r.period_id,
                  array_agg(r.quality_id) quality_id
                FROM (SELECT
                        CASE WHEN ppc.specialist_id IS NOT null THEN ppc.specialist_id
                        ELSE
                          CASE WHEN site.specialist_id IS NOT null THEN site.specialist_id
                          ELSE
                            CASE WHEN smm.specialist_id IS NOT null THEN smm.specialist_id
                            ELSE
                              CASE WHEN seo.specialist_id IS NOT null THEN seo.specialist_id END END END END specialist,
                        rpqc.id quality_id,
                        k.name period_name,
                        k.id period_id

                      FROM process_launch pl
                        LEFT JOIN process_ppc ppc
                          ON (pl.id = ppc.launch_id)
                        LEFT JOIN process_site site
                          ON (pl.id = site.launch_id)
                        LEFT JOIN process_seo seo
                          ON (pl.id = seo.launch_id)
                        LEFT JOIN process_smm smm
                          ON (pl.id = smm.launch_id)
                        JOIN res_partner_quality_control AS rpqc
                          ON (rpqc.partner_id = pl.partner_id)
                        JOIN kpi_period k
                          ON (k.id = rpqc.period_id)
                     ) r
                GROUP BY r.specialist, r.period_id, r.period_name
            )
        """)


ReportQualityControlSpecialist()