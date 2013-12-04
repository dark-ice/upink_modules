# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model

STAGES = (
    ('planning', 'Проектирование'),
    ('design', 'Дизайн'),
    ('makeup', 'Верстка'),
    ('developing', 'Программирование'),
    ('testing', 'Тестирование'),
)


class ReportDaySite(Model):
    _name = "report.day.site"
    _description = u"Отчет по сайтам"
    _auto = False
    _order = "launch_id"

    def _get_data(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, [
            'partner_id',
            'design_date_st',
            'design_date_fn',
            'planning_date_st',
            'planning_date_fn',
            'makeup_date_st',
            'makeup_date_fn',
            'developing_date_st',
            'developing_date_fn',
            'testing_date_st',
            'testing_date_fn',
        ], context):

            process_name = '-'
            process_date = ''
            if context.get('date'):
                if record['design_date_fn']:
                    if record['design_date_st'] <= context['date'] <= record['design_date_fn']:
                        process_name = 'Дизайн'
                        process_date = record['design_date_fn']
                elif record['design_date_st']:
                    if record['design_date_st'] <= context['date']:
                        process_name = 'Дизайн'
                        process_date = record['design_date_fn']

                if record['planning_date_fn']:
                    if record['planning_date_st'] <= context['date'] <= record['planning_date_fn']:
                        process_name = 'Проектирование'
                        process_date = record['planning_date_fn']
                elif record['planning_date_st']:
                    if record['planning_date_st'] <= context['date']:
                        process_name = 'Проектирование'
                        process_date = record['planning_date_fn']

                if record['makeup_date_fn']:
                    if record['makeup_date_st'] <= context['date'] <= record['makeup_date_fn']:
                        process_name = 'Верстка'
                        process_date = record['makeup_date_fn']
                elif record['makeup_date_st']:
                    if record['makeup_date_st'] <= context['date']:
                        process_name = 'Верстка'
                        process_date = record['makeup_date_fn']

                if record['developing_date_fn']:
                    if record['developing_date_st'] <= context['date'] <= record['developing_date_fn']:
                        process_name = 'Программирование'
                        process_date = record['developing_date_fn']
                elif record['developing_date_st']:
                    if record['developing_date_st'] <= context['date']:
                        process_name = 'Программирование'
                        process_date = record['developing_date_fn']

                if record['testing_date_fn']:
                    if record['testing_date_st'] <= context['date'] <= record['testing_date_fn']:
                        process_name = 'Тестирование'
                        process_date = record['testing_date_fn']
                elif record['testing_date_st']:
                    if record['testing_date_st'] <= context['date']:
                        process_name = 'Тестирование'
                        process_date = record['testing_date_fn']

            res[record['id']] = {
                'process_name': process_name,
                'process_date': process_date,
            }
        return res

    _columns = {
        'launch_id': fields.integer('id'),
        'partner_id': fields.many2one('res.partner', "Проект"),

        'process_name': fields.function(
            _get_data,
            type='char',
            selection=STAGES,
            multi='need_date',
            string='Текущий этап',
        ),
        'process_date': fields.function(
            _get_data,
            type='date',
            multi='need_date',
            string='Дата завершения',
        ),

        'type': fields.char('', size=8),
        'planning_days': fields.integer('П'),
        'design_days': fields.integer('Д'),
        'makeup_days': fields.integer('В'),
        'developing_days': fields.integer('П'),
        'testing_days': fields.integer('Т'),

        'design_stage': fields.selection(STAGES, 'Дизайн'),
        'planning_stage': fields.selection(STAGES, 'Проектирование'),
        'makeup_stage': fields.selection(STAGES, 'Верстка'),
        'developing_stage': fields.selection(STAGES, 'Программирование'),
        'testing_stage': fields.selection(STAGES, 'Тестирование'),

        'design_date_st': fields.date('Дизайн старт'),
        'planning_date_st': fields.date('Планирование старт'),
        'makeup_date_st': fields.date('Верстка старт'),
        'developing_date_st': fields.date('Программирование старт'),
        'testing_date_st': fields.date('Тестирование старт'),

        'design_date_fn': fields.date('Дизайн завершение'),
        'planning_date_fn': fields.date('Планирование завершение'),
        'makeup_date_fn': fields.date('Верстка завершение'),
        'developing_date_fn': fields.date('Программирование завершение'),
        'testing_date_fn': fields.date('Тестирование завершение'),

        'date_end': fields.date('Production'),
        'search_date': fields.date('Дата для поиска')
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_day_site')
        cr.execute("""
            create or replace view report_day_site as (
                SELECT
                    row_number() over() as id,
                       r.*
                from (
                    SELECT
                      pl.id as launch_id,
                      pl.partner_id,
                      max(CASE when pss.stage = 'design' then 'design' else Null end) design_stage,
                      max(CASE when pss.stage = 'design' then pss.plan_date_st else Null end) design_date_st,
                      max(CASE when pss.stage = 'design' then pss.plan_date_fn else Null end) design_date_fn,
                      max(CASE when pss.stage = 'design' then (pss.plan_date_fn - pss.plan_date_st) else Null end) design_days,

                      max(CASE when pss.stage = 'planning' then 'planning' else Null end) planning_stage,
                      max(CASE when pss.stage = 'planning' then pss.plan_date_st else Null end) planning_date_st,
                      max(CASE when pss.stage = 'planning' then pss.plan_date_fn else Null end) planning_date_fn,
                      max(CASE when pss.stage = 'planning' then (pss.plan_date_fn - pss.plan_date_st) else Null end) planning_days,

                      max(CASE when pss.stage = 'makeup' then 'makeup' else Null end) makeup_stage,
                      max(CASE when pss.stage = 'makeup' then pss.plan_date_st else Null end) makeup_date_st,
                      max(CASE when pss.stage = 'makeup' then pss.plan_date_fn else Null end) makeup_date_fn,
                      max(CASE when pss.stage = 'makeup' then (pss.plan_date_fn - pss.plan_date_st) else Null end) makeup_days,

                      max(CASE when pss.stage = 'developing' then 'developing' else Null end) developing_stage,
                      max(CASE when pss.stage = 'developing' then pss.plan_date_st else Null end) developing_date_st,
                      max(CASE when pss.stage = 'developing' then pss.plan_date_fn else Null end) developing_date_fn,
                      max(CASE when pss.stage = 'developing' then (pss.plan_date_fn - pss.plan_date_st) else Null end) developing_days,

                      max(CASE when pss.stage = 'testing' then 'testing' else Null end) testing_stage,
                      max(CASE when pss.stage = 'testing' then pss.plan_date_st else Null end) testing_date_st,
                      max(CASE when pss.stage = 'testing' then pss.plan_date_fn else Null end) testing_date_fn,
                      max(CASE when pss.stage = 'testing' then (pss.plan_date_fn - pss.plan_date_st) else Null end) testing_days,

                      max(ps.date_end) as date_end,
                      max(ps.date_end) as search_date,
                      'П' as type


                    from process_site ps
                    join process_launch pl
                      on (pl.id = ps.launch_id)
                    join process_site_stage pss
                      on (pss.site_id = ps.id)

                    where pss.plan_date_fn is not NULL and pss.plan_date_st is not NULL
                    group by pl.id

                UNION

                SELECT
                      pl.id as launch_id,
                      pl.partner_id,
                      max(CASE when pss.stage = 'design' then 'design' else Null end) design_stage,
                      max(CASE when pss.stage = 'design' then pss.real_date_st else Null end) design_date_st,
                      max(CASE when pss.stage = 'design' then pss.real_date_fn else Null end) design_date_fn,
                      max(CASE when pss.stage = 'design' then (pss.real_date_fn - pss.real_date_st) else Null end) design_days,

                      max(CASE when pss.stage = 'planning' then 'planning' else Null end) planning_stage,
                      max(CASE when pss.stage = 'planning' then pss.real_date_st else Null end) planning_date_st,
                      max(CASE when pss.stage = 'planning' then pss.real_date_fn else Null end) planning_date_fn,
                      max(CASE when pss.stage = 'planning' then (pss.real_date_fn - pss.real_date_st) else Null end) planning_days,

                      max(CASE when pss.stage = 'makeup' then 'makeup' else Null end) makeup_stage,
                      max(CASE when pss.stage = 'makeup' then pss.real_date_st else Null end) makeup_date_st,
                      max(CASE when pss.stage = 'makeup' then pss.real_date_fn else Null end) makeup_date_fn,
                      max(CASE when pss.stage = 'makeup' then (pss.real_date_fn - pss.real_date_st) else Null end) makeup_days,

                      max(CASE when pss.stage = 'developing' then 'developing' else Null end) developing_stage,
                      max(CASE when pss.stage = 'developing' then pss.real_date_st else Null end) developing_date_st,
                      max(CASE when pss.stage = 'developing' then pss.real_date_fn else Null end) developing_date_fn,
                      max(CASE when pss.stage = 'developing' then (pss.real_date_fn - pss.real_date_st) else Null end) developing_days,

                      max(CASE when pss.stage = 'testing' then 'testing' else Null end) testing_stage,
                      max(CASE when pss.stage = 'testing' then pss.real_date_st else Null end) testing_date_st,
                      max(CASE when pss.stage = 'testing' then pss.real_date_fn else Null end) testing_date_fn,
                      max(CASE when pss.stage = 'testing' then (pss.real_date_fn - pss.real_date_st) else Null end) testing_days,

                      max(ps.date_end) as date_end,
                      max(ps.date_end) as search_date,
                      'Ф' as type

                    from process_site ps
                    join process_launch pl
                      on (pl.id = ps.launch_id)
                    join process_site_stage pss
                      on (pss.site_id = ps.id)

                    where pss.plan_date_fn is not NULL and pss.plan_date_st is not NULL
                    group by pl.id) as r order by r.launch_id, r.type
            )""")

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if args:
            if context is None:
                context = dict()
            i = 0
            for record in args:
                if record[0] == 'search_date':
                    context['date'] = record[2]
                    del args[i]
                i += 1

        return super(ReportDaySite, self).search(cr, user, args, offset, limit, order, context, count)


ReportDaySite()