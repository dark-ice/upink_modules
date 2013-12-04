# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportDayCallInStatistic(Model):
    _name = "report.day.call.in.static"
    _description = u"доп модель отчета по направлению call"
    _order = 'date DESC'

    _columns = {
        'process_call_in_id': fields.many2one('process.call.in', 'Проект', domain="[('state', '=', 'development')]"),
        'supervisor_id': fields.related(
            'process_call_in_id',
            'specialist_id',
            type='many2one',
            relation='res.users',
            string='Супервайзер проекта',
            select=True,
            domain="[('groups_id','in',[103])]",
        ),
        'date': fields.date('Дата'),
        'call_in': fields.integer('Принятые'),
        'call_in_day': fields.integer('Принятые день'),
        'call_in_night': fields.integer('Принятые ночь'),
        'missed': fields.integer('Пропущенные'),
        'missed_day': fields.integer('Пропущенные день'),
        'missed_night': fields.integer('Пропущенные ночь'),
        'call_out': fields.integer('Исходящие'),
        'processed_missed': fields.integer('Обработанные пропущенные'),

    }

ReportDayCallInStatistic()


class ReportDayCallIn(Model):
    _name = "report.call.in"
    _description = u"Отчет по входящим проектам"
    _auto = False
    _order = 'date'

    #def _get_dop_data(self, cr, uid, ids, name, arg, context=None):
    #    res = {}
    #    procent = 0.0
    #    for record in self.read(cr, uid, ids, ['call_in', 'missed'], context=context):
    #        res[record['id']] = 0.0
    #        if record['call_in']:
    #            procent = float(record['missed'])/record['call_in'] + record['call_in']
    #        res[record['id']] = procent
    #    return res

    _columns = {
        'date_start': fields.date('Дата начала'),
        'date_end': fields.date('Дата конца'),

        'partner_id': fields.many2one('res.partner', "Проект"),
        'call_in': fields.integer('Принятые', group_operator='sum'),
        'missed': fields.integer('Пропущенные', group_operator='sum'),
        'date': fields.date('Дата'),
        'procent': fields.float('Процент', group_operator='avg'),
        'procent_day': fields.float('Процент день', group_operator='avg'),
        'procent_night': fields.float('Процент ночь', group_operator='avg'),
        'queue': fields.integer('Очередь'),
        'call_in_day': fields.integer('Принятые день' , group_operator='sum'),
        'call_in_night': fields.integer('Принятые ночь'),
        'missed_day': fields.integer('Пропущенные день'),
        'missed_night': fields.integer('Пропущенные ночь'),
        'call_out': fields.integer('Исходящие', group_operator='sum'),
        'processed_missed': fields.integer('Обработанные пропущенные', group_operator='sum'),

    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_call_in')
        cr.execute("""
            create or replace view report_call_in as (
                SELECT
                    row_number() over() as id,
                    l.partner_id,
                    c.queue,
                    s.date,
                    s.date date_start,
                    s.date date_end,
                    s.call_in,
                    s.missed,
                    s.call_in_day,
                    s.call_in_night,
                    s.missed_day,
                    s.missed_night,
                    s.call_out,
                    s.processed_missed,
                    (cast(missed as real)/(cast(call_in as real)+cast(missed as real))) as procent,
                    (cast(missed_day as real)/(cast(call_in_day as real)+cast(missed_day as real))) as procent_day,
                    (cast(missed_night as real)/(cast(call_in_night as real)+cast(missed_night as real))) as procent_night
                FROM process_call_in c
                LEFT JOIN process_launch l on (c.launch_id=l.id)
                LEFT JOIN report_day_call_in_static s on (s.process_call_in_id=c.id)
                WHERE c.state in ('development', 'pause', 'coordination_reporting', 'finish')
            )""")

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        for item in args:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
        return super(ReportDayCallIn, self).search(cr, user, args, offset, limit, order, context, count)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for item in domain:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
        return super(ReportDayCallIn, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)

ReportDayCallIn()