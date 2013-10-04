# coding=utf-8
__author__ = 'skripnik'
from datetime import datetime
import pytz
from openerp.osv.orm import TransientModel
from openerp.osv import fields


class grade_wizard(TransientModel):
    # позволяет собрать данные из разных таблиц в некую виртуальную сущность
    # которую мы не храним но можем к ней обратится
    _name = 'grade.wizard'
    _columns = {
        'dy_cash': fields.float('Текущее начисление', readonly=True),
        'grade_id': fields.many2one('kpi.grade', 'Текущий грейд', readonly=True),
        'next_grade_id': fields.many2one('kpi.grade', 'Новый грейд', required=True),
        'history_date': fields.date('Дата изменения', required=True),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник'),
        'next_dy_cash': fields.float('Новое начисление')
    }

    _defaults = {
        'employee_id': lambda s, cr, u, cnt: cnt.get('employee_id'),
        'dy_cash': lambda s, cr, u, cnt: cnt.get('dy_cash'),
        'grade_id': lambda s, cr, u, cnt: cnt.get('grade_id'),
        'history_date': lambda *a: datetime.now(pytz.utc).strftime("%Y-%m-%d")
    }

    def get_period(self, cr, uid, ids, date, employee_id):
        grade_id, dy_cash = self.pool.get('kpi.grade.history').get_grade(cr, date, employee_id)
        return {'value': {'dy_cash': dy_cash, 'grade_id': grade_id}}

    def change_neighboring_grade_history(self, cr, date, employee_id, next_dy_cash, next_grade_id):
        kpi_grade_obj = self.pool.get('kpi.grade.history')
        period = kpi_grade_obj.get_period(cr, date, employee_id)
        history_ids = kpi_grade_obj.search(cr, 1, [('employee_id', '=', employee_id), ('period_id.name', '>', period.name)])
        if history_ids:
            kpi_grade_obj.write(cr, 1, [history_ids[-1]], {'grade_id': next_grade_id, 'dy_cash': next_dy_cash})

    def save_grade_date(self, cr, uid, ids, context=None):
        kpi_grade_obj = self.pool.get('kpi.grade.history')
        for record in self.browse(cr, uid, ids):
            grade_id, dy_cash = kpi_grade_obj.get_grade(cr, record.history_date, record.employee_id.id)
            self.change_neighboring_grade_history(cr, record.history_date, record.employee_id.id, record.next_dy_cash, record.next_grade_id.id)
            kpi_grade_obj.create(cr, uid, {
                'next_grade_id': record.next_grade_id.id,
                'history_date': record.history_date,
                'next_dy_cash': record.next_dy_cash,
                'employee_id': record.employee_id.id,
                'dy_cash': dy_cash,
                'grade_id': grade_id
            })
        return {'type': 'ir.actions.act_window_close'}


grade_wizard()
