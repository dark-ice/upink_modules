# -*- coding: utf-8 -*-

from osv import osv
from osv import fields


class income_report_print(osv.osv_memory):
    _name = 'income.report.print'
    _description = 'Object for printing income report by period'

    def print_report(self, cr, uid, ids, context=None):
        """
            Вызов метода происходит из wizard.
            Происходит поиск ids по определенному периоду
                ids преобразовываются в строку, так принимает report_aeroo
            Через context['active_id'] передается id отчета
            Вызывает функцию report_aeroo модуля to_print:
                которая генерит отчет с полями указанными во view для этого обьекта
        """
        data = self.browse(cr, uid, ids[0], context)
        values = {}
        object_ids = self.pool.get('income.report').search(cr, uid, [('period_id', '=', data.period_id.name)])
        if not object_ids:
            raise osv.except_osv("Пустая выборка", "В выборке нет данных")
        else:
            print_ids = str(object_ids)[1:-1]
        values = {'object_ids': print_ids, 'name': 'income.report'}
        id = self.pool.get('aeroo.print_by_action').create(cr, uid, values, context)
        context['active_model'] = 'ir.actions.report.xml'
        report_data = self.pool.get('ir.actions.report.xml').search(cr, uid, [('model', '=', 'income.report')])
        context['active_id'] = report_data[0]
        return self.pool.get('aeroo.print_by_action').to_print(cr, uid, [id], context)

    _columns = {
        'period_id': fields.many2one('kpi.period', u'Период', required=True),
    }

income_report_print()


class income_report(osv.osv):
    _name = 'income.report'

    _columns = {
        'kpi_id': fields.many2one('kpi.kpi', u'KPI', invisible=True),
        'period_id': fields.char(u'Период', size=50),
        'grade': fields.char(u'Грэйд', size=30),
        'employee_id': fields.char(u'Сотрудник', size=100),
        'job_id': fields.char(u'Должность', size=255),
        'sv': fields.char(u'Разбивка', size=10),
        'total_pay': fields.float(u'К начислению', digits=(10, 2)),
        'formal_cash': fields.float(u'Официальная ЗП', digits=(10, 2)),
        'formal_tax': fields.float(u'Налог с официальной ЗП', digits=(10, 2)),
        'days_worked': fields.integer(u'Количество отработанных дней'),
        'retention': fields.float(u"Удержания"),
        'advance': fields.float(u"Аванс"),
        'award': fields.float(u'Премия'),
    }

income_report()
