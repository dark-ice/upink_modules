# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model
import pytz


class ReportDaySmmStatisticPlan(Model):
    _name = "report.day.smm.static.plan"
    _description = u"доп модель отчета по направлению smm план"
    _rec_name = 'id'
    _columns = {
        'process_smm_id': fields.many2one('process.smm', 'Проект', domain="[('state', '=', 'work')]"),
        'kpi_index': fields.many2one('process.sla.indicators', 'KPI Показатель', domain="[('type', '=', 'smm')]"),
        'kpi_target': fields.float('Цель по KPI'),
        'work_start': fields.date('Старт работы'),
        'report': fields.char('Отчет', size=256),
        'date_start': fields.date('Дата начала периода'),
        'date_end': fields.date('Дата конца периода'),
        'supervisor_id': fields.related(
            'process_smm_id',
            'specialist_id',
            type='many2one',
            relation='res.users',
            string='Специалист',
            select=True,
            domain="[('groups_id','in',[80])]",
        ),
    }


ReportDaySmmStatisticPlan()


class ReportDaySmmStatisticFact(Model):
    _name = "report.day.smm.static.fact"
    _description = u"доп модель отчета по направлению smm факт"
    _rec_name = 'id'
    _columns = {
        'process_smm_id': fields.many2one('process.smm', 'Проект', domain="[('state', '=', 'work')]"),
        'date': fields.date('Дата'),
        'kpi_index': fields.many2one('process.sla.indicators', 'Показатель KPI', domain="[('type', '=', 'smm')]"),
        'index_point': fields.float('Значение показателя'),
        'supervisor_id': fields.related(
            'process_smm_id',
            'specialist_id',
            type='many2one',
            relation='res.users',
            string='Специалист',
            select=True,
            domain="[('groups_id','in',[80])]",
        ),
    }


ReportDaySmmStatisticFact()


class ReportDaySmm(Model):
    _name = "report.day.smm"
    _description = u"Отчет по smm"
    _auto = False

    def _get_data(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['partner_id', 'kpi_index', 'date_start_plan'], context):
            if record.get('partner_id') and record.get('kpi_index') and record.get('date_start_plan'):
                records_ids = self.search(cr, 1, [
                    ('partner_id', '=', record['partner_id'][0]),
                    ('kpi_index', '=', record['kpi_index'][0]),
                    ('date_start_plan', '=', record['date_start_plan'])
                ])
                need_sum = 0.0
                for one_id in records_ids:
                    point = self.read(cr, uid, one_id, ['index_point'])
                    need_sum += point['index_point']
                    res[record['id']] = {
                        'index_point_for_current': need_sum,
                    }
        return res

    _columns = {
        'date_start': fields.date('Дата начала'),
        'date_end': fields.date('Дата конца'),

        'plan_id': fields.many2one('report.day.smm.static.plan', 'id плана'),
        'partner_id': fields.many2one('res.partner', "Проект"),
        'date': fields.date('Дата'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'work_start': fields.date('Старт работы'),
        'report': fields.char('Отчет', size=256),
        'date_start_plan': fields.date('Дата начала периода'),
        'date_end_plan': fields.date('Дата конца периода'),
        'kpi_index': fields.many2one('process.sla.indicators', 'Показатель KPI', domain="[('type', '=', 'smm')]"),
        'kpi_target': fields.float('Цель по KPI'),
        'old_point': fields.float('Значение показателя за предыдущий период'),
        'index_point': fields.float('Значение показателя'),
        'index_point_for_current': fields.function(
            _get_data,
            type='float',
            multi='need_date',
            string='Значение показателя за текущий период',
        )
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_day_smm')
        cr.execute("""
            create or replace view report_day_smm as (
                SELECT
                    row_number() over() as id,

                    sf.date date_start,
                    sf.date date_end,

                    l.partner_id,
                    l.service_id,
                    sp.work_start,
                    sp.report,
                    sp.date_start date_start_plan,
                    sp.date_end date_end_plan,
                    sp.kpi_index,
                    sp.kpi_target,
                    o.fact old_point,
                    sf.index_point,
                    sf.date::date,
                    sp.id plan_id

                FROM report_day_smm_static_plan sp
                LEFT JOIN  process_smm s on (sp.process_smm_id=s.id)
                LEFT JOIN process_launch l on (s.launch_id=l.id)
                LEFT JOIN report_day_smm_static_fact sf on (sf.process_smm_id=s.id AND sp.kpi_index=sf.kpi_index AND sf.date >= sp.date_start AND sf.date <= sp.date_end)
                LEFT JOIN (
                SELECT
                  p1.id,
                  sum(f.index_point) fact
                FROM report_day_smm_static_plan p1
                  LEFT JOIN (
                    SELECT
                      f1.process_smm_id,
                      f1.kpi_index,
                      index_point,
                      date,
                      p2.id plan_id,
                      p2.date_end
                    FROM report_day_smm_static_fact f1
                    LEFT JOIN report_day_smm_static_plan p2 on (p2.process_smm_id=f1.process_smm_id AND p2.kpi_index=f1.kpi_index AND f1.date >= p2.date_start AND f1.date <= p2.date_end)
                  ) f on (f.process_smm_id = p1.process_smm_id AND f.kpi_index = p1.kpi_index AND f.date_end < p1.date_start)
                GROUP BY p1.id) o on (o.id=sp.id)
                WHERE s.state in ('work')
            )""")

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        index_list = list()

        date_start = ''
        date_end = ''
        for k, item in enumerate(args):
            if item[0] == 'date_start':
                index_list.append(k)
                date_start = item[2]
            if item[0] == 'date_end':
                index_list.append(k)
                date_end = item[2]

        for index in reversed(index_list):
            del args[index]
        if not date_start and date_end:
            date_start = datetime.now(pytz.utc)
        if not date_end and date_start:
            date_end = datetime.now(pytz.utc)

        if date_end:
            args.extend(['&', ['date_start_plan', '>=', date_start], ['date_start_plan', '<=', date_end]])
        if date_start:
            args.extend(['&', ['date_end_plan', '>=', date_start], ['date_end_plan', '<=', date_end]])
        if date_start and date_end:
            args = ['|'] + args

        return super(ReportDaySmm, self).search(cr, user, args, offset, limit, order, context, count)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for item in domain:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
        return super(ReportDaySmm, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)


ReportDaySmm()