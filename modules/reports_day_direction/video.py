# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model

STATES = (
    ('coordination', 'Согласование заявки на запуск'),
    ('filling_TK', 'Заполнение ТЗ'),
    ('matching_TK', 'Согласование ТЗ'),
    ('development', 'Разработка идей'),
    ('selection', 'Выбор идеи'),
    ('drawing_up', 'Составление сценария'),
    ('matching_script', 'Согласование сценария'),
    ('signing_application', 'Подписание приложения к договору'),
    ('preparation', 'Подготовительные работы к разработке проекта'),
    ('approval', 'Согласование вариантов'),
    ('work', 'Работа над проектом'),
    ('assertion', 'Утверждение заказчиком'),
    ('transmission', 'Передача проекта'),
    ('finish', 'Проект передан'),
    ('cancel', 'Отмена'),
)

WORK_STATES = (
    ('graphic', 'Графика'),
    ('speaker', 'Дикторы'),
    ('actor', 'Актеры'),
    ('music', 'Музыкальное решение'),
)


class ReportDayVideo(Model):
    _name = "report.day.video"
    _description = u"Отчет по video"
    _auto = False
    _columns = {
        'partner_id': fields.many2one('res.partner', "Партнер"),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'state': fields.selection(STATES, 'Статус'),
        'work_state': fields.selection(WORK_STATES, 'Статус работы')
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_day_video')
        cr.execute("""
            create or replace view report_day_video as (
                SELECT
                    row_number() over() as id,
                        l.service_id,
                        l.partner_id,
                        pv.work_state,
                        pv.state
                    from process_video pv
                    LEFT JOIN process_launch l on (pv.launch_id=l.id)
            )""")

ReportDayVideo()