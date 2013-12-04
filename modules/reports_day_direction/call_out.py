# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class ReportDayCallOutStatistic(Model):
    _name = "report.day.call.out.static"
    _description = u"доп модель отчета по направлению call"

    _columns = {
        'process_call_out_id': fields.many2one('process.call.out', 'Проект', domain="[('state', '=', 'development')]"),
        'supervisor_id': fields.related(
            'process_call_out_id',
            'specialist_id',
            type='many2one',
            relation='res.users',
            string='Супервайзер проекта',
            select=True,
            domain="[('groups_id','in',[103])]",
        ),
        'target_date_start': fields.char('Плановая дата запуска', size=1024),
        'target_date_end': fields.char('Плановая дата завершения', size=1024),
        'date': fields.date('Дата'),
        'coll_num': fields.integer('Количество звонков'),
        'contact_end_status_num': fields.integer('Контактов с конечным статусом'),
        'partner_give': fields.integer('Передано Партнеру')
    }


ReportDayCallOutStatistic()


class ReportDayCallOut(Model):
    _name = "report.call.out"
    _description = u"Отчет по исходящим проектам"
    _auto = False
    _order = 'date'

    def _get_data(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['partner_id'], context):
            if record.get('partner_id'):
                records_ids = self.search(cr, 1, [('partner_id', '=', record['partner_id'][0])])
                contact_end_status_num_sum = 0.0
                partner_give_sum = 0.0
                for one_id in records_ids:
                    data = self.read(cr, uid, one_id, ['partner_give', 'contact_end_status_num'])
                    contact_end_status_num_sum += data['contact_end_status_num']
                    partner_give_sum += data['partner_give']
                res[record['id']] = {
                    'current_conversion_general': (partner_give_sum / contact_end_status_num_sum),
                }
        return res

    _columns = {
        'date_start': fields.date('Дата начала'),
        'date_end': fields.date('Дата конца'),

        'partner_id': fields.many2one('res.partner', "Проект"),
        'date': fields.date('дата'),
        'target_date_start': fields.char('Плановая дата запуска', size=1024),
        'target_date_end': fields.char('Плановая дата завершения', size=1024),
        'contact_num': fields.integer('Всего контактов для прозвона', group_operator='avg'),
        'contact_end_status_num': fields.integer('С конечным статусом', group_operator='sum'),
        'coll_num': fields.integer('Совершено звонков', group_operator='sum'),
        'conversion': fields.float('Конверсия', group_operator='sum'),
        'current_conversion': fields.float('Текущая конверсия'),
        'partner_give': fields.integer('Передано Партнеру'),
        'current_conversion_general': fields.function(
            _get_data,
            type='float',
            multi='need_date',
            string='Текущая конверсия (итого)',
            group_operator='avg'
        )
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_call_out')
        cr.execute("""
            create or replace view report_call_out as (
                SELECT
                    row_number() over() as id,
                    l.partner_id,
                    s.date,

                    s.date date_start,
                    s.date date_end,

                    s.target_date_start,
                    s.target_date_end,
                    c.contact_num,
                    s.contact_end_status_num,
                    s.coll_num,
                    s.partner_give,

                    (cast(s.partner_give as real)/cast(c.contact_num as real)) as conversion,
                    (cast(s.partner_give as real)/cast(s.contact_end_status_num as real)) as current_conversion

                FROM process_call_out c
                LEFT JOIN process_launch l on (c.launch_id=l.id)
                LEFT JOIN report_day_call_out_static s on (s.process_call_out_id=c.id)
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
        return super(ReportDayCallOut, self).search(cr, user, args, offset, limit, order, context, count)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for item in domain:
            if item[0] == 'date_start':
                item[0] = 'date'
                item[1] = '>='

            if item[0] == 'date_end':
                item[0] = 'date'
                item[1] = '<='
        return super(ReportDayCallOut, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context,
                                                        orderby)


ReportDayCallOut()