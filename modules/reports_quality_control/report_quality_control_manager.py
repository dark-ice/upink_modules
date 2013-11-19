# coding=utf-8
import calendar
import numpy
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportQualityControlManager(Model):
    _name = "report.quality.control.manager"
    _rec_name = 'partner_id'
    _auto = False

    def _get_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['quality_ids'], context):

            ydolit = self.pool.get('res.partner.quality.control')._get_ydolit(cr, uid, record['quality_ids'], '', {}, context=None)
            points = []
            indexes = []
            for k, val in ydolit.iteritems():
                points.append(val['level_ydolit'])
                indexes.append(val['index_ydolit'])

            res[record['id']] = {
                'quality_point': numpy.mean(points),
                'quality_index': numpy.mean(indexes),
                'services_cnt': len(record['quality_ids']),
            }
        return res

    _columns = {
        'manager_id': fields.many2one('res.users', 'Менеджеры'),
        'services_cnt': fields.function(
            _get_date,
            type='integer',
            multi='need_date',
            string='Количество услуг',
        ),
        'quality_point': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Уровень удовлетворенности',
        ),
        'quality_index': fields.function(
            _get_date,
            type='float',
            multi='need_date',
            string='Индекс удовлетворенности',
        ),
        'mbo': fields.float('MBO по услуге'),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'period_name': fields.char('Период', size=10),
        'quality_ids': fields.integer('id оценки услуги'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_quality_control_manager')
        cr.execute("""
            create or replace view report_quality_control_manager as (
                SELECT
                  row_number() over() as id,
                  r.manager_id,
                  r.period_id,
                  r.period_name,
                  avg(r.mbo) mbo,
                  array_agg(r.quality_id) quality_ids
                FROM (
                  SELECT
                    rpqc.period_id,
                    k.name period_name,
                    case when th.name is null then p.user_id else th.name end manager_id,
                    rpqc.mbo,
                    rpqc.id quality_id
                    FROM res_partner_quality_control AS rpqc
                    LEFT JOIN res_partner p on (p.id=rpqc.partner_id)
                    LEFT JOIN kpi_period k
                      ON (k.id = rpqc.period_id)
                    LEFT JOIN transfer_history AS th
                      ON (th.partner_id = rpqc.partner_id AND (k.name>=to_char(th.create_date, 'YYYY/MM')) AND k.name<(SELECT to_char(th2.create_date, 'YYYY/MM') FROM transfer_history th2 WHERE th2.partner_id = rpqc.partner_id AND th2.create_date > th.create_date LIMIT 1))) r
                GROUP BY r.manager_id, r.period_id,  r.period_name
            )
        """)


ReportQualityControlManager()