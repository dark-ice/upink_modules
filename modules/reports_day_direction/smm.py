# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportDaySmmStatisticPlan(Model):
    _name = "report.day.smm.static.plan"
    _description = u"доп модель отчета по направлению smm план"
    _columns = {
        'process_smm_id': fields.many2one('process.smm', 'Проект', domain="[('state', '=', 'work')]"),
        'kpi_index': fields.many2one('process.sla.indicators', 'KPI Показатель', domain="[('type', '=', 'smm')]"),
        'kpi_target': fields.float('Цель по KPI'),
        'work_start': fields.date('Старт работы'),
        'report': fields.char('Отчет', size=256),
        'date_start': fields.date('Дата начала проекта'),
        'date_end': fields.date('Дата конца проекта'),
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
    _name = "report.smm"
    _description = u"Отчет по smm"
    _auto = False

    _columns = {
        'date_start': fields.date('Дата начала'),
        'date_end': fields.date('Дата конца'),

        'partner_id': fields.many2one('res.partner', "Проект"),
        'date': fields.date('Дата'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'work_start': fields.date('Начало работы'),
        'report': fields.char('Отчет', size=256),
        'date_start_plan': fields.date('Дата начала'),
        'kpi_index': fields.many2one('process.sla.indicators', 'Показатель KPI', domain="[('type', '=', 'smm')]"),
        'kpi_target': fields.float('Цель по KPI'),
        'old_point': fields.float('Показатель за прошедший период', group_operator='sum'),
        'index_point': fields.float('Значение показателя', group_operator='sum'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_smm')
        cr.execute("""
            create or replace view report_smm as (
                SELECT
                    row_number() over() as id,

                    sp.date_start date_start,
                    sp.date_start date_end,

                    l.partner_id,
                    l.service_id,
                    sf.work_start,
                    sf.report,
                    sp.date_start date_start_plan,
                    sp.kpi_index,
                    sp.kpi_target,
                    (select old.index_point from report_day_smm_static_fact old where old.work_start < sf.work_start and old.process_smm_id = sf.process_smm_id limit 1) as old_point,
                    sf.index_point,
                    sf.date

            FROM process_smm s
            LEFT JOIN process_launch l on (s.launch_id=l.id)
            JOIN report_day_smm_static_plan sp on (sp.process_smm_id=s.id)
            JOIN report_day_smm_static_fact sf on (sf.process_smm_id=s.id)
            WHERE s.state in ('work')
            )""")

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        for item in args:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
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