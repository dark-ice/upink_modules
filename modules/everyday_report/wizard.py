# coding=utf-8
from openerp.osv import osv, fields
from openerp.osv.orm import TransientModel


class WizardSource(TransientModel):
    _name = 'day.report.wizard'
    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),
    }

    def print_report(self, cr, uid, ids, context=None):
        """
            Вызов метода происходит из wizard.
            Происходит поиск ids по определенному периоду
                ids преобразовываются в строку, так принимает report_aeroo
            Через context['active_id'] передается id отчета
            Вызывает функцию report_aeroo модуля to_print:
                которая генерит отчет с полями указанными во view для этого обьекта
        """
        if context is None:
            context = {}

        data = self.browse(cr, uid, ids[0], context)

        model = context.get('model')
        if not model:
            raise osv.except_osv("Модель не получена")

        object_ids = self.pool.get(model).search(cr, uid, [['date_start', '=', data.date_start], ['date_end', '=', data.date_end]])
        if not object_ids:
            raise osv.except_osv("Пустая выборка", "В выборке нет данных")
        else:
            print_ids = ', '.join(map(str, object_ids))

        values = {'object_ids': print_ids, 'name': model}
        a_id = self.pool.get('aeroo.print_by_action').create(cr, uid, values, context)
        report_data = self.pool.get('ir.actions.report.xml').search(cr, uid, [('model', '=', model)])

        context.update({
            'active_model': 'ir.actions.report.xml',
            'active_id': report_data[0],
            'ids': object_ids,
        })
        return self.pool.get('aeroo.print_by_action').to_print(cr, uid, [a_id], context)
WizardSource()
