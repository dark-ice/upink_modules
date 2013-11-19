# coding=utf-8
import calendar
import numpy
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportQualityControlPartner(Model):
    _name = "report.quality.control.partner"
    _auto = False

    def _get_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['quality_ids'], context):
            ydolit = self.pool.get('res.partner.quality.control')._get_ydolit(cr, uid, tuple(set(record['quality_ids'])), '', {},
                                                                              context=None)
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
                'mbo': numpy.mean(mbo),
            }
        return res

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Партнеры'),
        'direction': fields.char('Направление', size=256),
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
        'count': fields.integer('Количество проектов'),
        'mbo': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='MBO по услуге',
        ),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'period_name': fields.char('Период', size=10),
        'quality_ids': fields.char('массив', size=256),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_quality_control_partner')
        cr.execute("""
            create or replace view report_quality_control_partner as (
                SELECT
                  row_number() over() as id,
                  bss.direction,
                  k.name period_name,
                  k.id period_id,
                  count(pl.id),
                  pl.partner_id,
                  array_agg(rpqc.id) quality_ids
                FROM process_launch as pl
                JOIN res_partner_quality_control AS rpqc
                  ON (rpqc.partner_id = pl.partner_id AND rpqc.service_id = pl.service_id)
                JOIN brief_services_stage as bss
                  ON (bss.id = pl.service_id)
                JOIN kpi_period k
                  ON (k.id = rpqc.period_id)

                GROUP BY pl.partner_id, bss.direction, k.name, k.id
            )
        """)


ReportQualityControlPartner()