# coding=utf-8
__author__ = 'skripnik'

from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class StatisticUserReport(Model):
    _name = 'statistic.user.report'
    _auto = False

    _columns = {
        'id': fields.integer('ID'),
        'name': fields.char('ФИО', size=128),
        'category': fields.char('Категория', size=128),
        'grade_name': fields.char('Грейд', size=256),
        'direction': fields.char('Направление', size=256),
        'position': fields.char('Должность', size=256),
        'start_date': fields.char('Дата выхода', size=256),
        'probation': fields.char('Испытательный срок', size=256),
        'formalized': fields.char('Официально оформлен', size=256),
        'account_number': fields.char('Номер карты', size=256),
        'bank_name': fields.char('Название банка', size=256),
        'account_number_2': fields.char('Номер карты(второй)', size=256),
        'bank_name_2': fields.char('Название банка(второе)', size=256),
        'active': fields.selection([('True', 'Активен'), ('False', 'Неактивен')], 'Активность')
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'statistic_user_report')
        cr.execute("""
            create or replace view statistic_user_report as (
            select
                row_number()
                OVER () AS id,
                name,
                category,
                grade_name,
                direction,
                position,
                start_date,
                probation,
                formalized,
                instate_date,
                account_number,
                bank_name,
                account_number_2,
                bank_name_2,
                active

            from(
            select

                  rr.name,
                  CASE
                    WHEN he.category='top' THEN 'ТОП-менеджер'
                    WHEN he.category='head' THEN 'Линейный руководитель'
                    WHEN he.category='leading' THEN 'Ведущий специалист'
                    WHEN he.category='specialist' THEN 'Специалист'
                    WHEN he.category='on probation' THEN 'Сотрудник на испытательном сроке'
                  END as category,
                  kg.name as grade_name,
                  hd.name as direction,
                  hj.name as position,
                  he.start_date,
                  CASE
                    WHEN he.category='on probation' THEN 'Да'
                    ELSE 'Нет'
                  END as probation,
                  CASE
                    WHEN he.formalized='True' THEN 'Да'
                    ELSE 'Нет'
                  END as formalized,
                  he.instate_date,
                  he.account_number,
                  he.bank_name,
                  he.account_number_2,
                  he.bank_name_2,
                  active

                from hr_employee as he
                left join resource_resource as rr
                on (he.resource_id = rr.id)

                left join grade_wizard as gw
                on (he.id = gw.employee_id and gw.history_date = (select max(g.history_date) from grade_wizard as g where g.employee_id = he.id))

                left join kpi_grade as kg
                on (kg.id = gw.grade_id)

                left join hr_department as hd
                on (hd.id = he.department_id)

                left join hr_job as hj
                on (hj.id = he.job_id)
            ) r
            )""")

StatisticUserReport();