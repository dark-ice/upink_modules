# coding=utf-8
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel


class HrCommittee(TransientModel):
    _name = 'hr.technique.committee'
    _description = u'Учет техники - Комиссия на списание - Wizard'

    _columns = {
        'technique_id': fields.many2one('hr.technique', 'Техника'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', required=True),
    }

    _defaults = {
        'technique_id': lambda cr, u, i, ctx: ctx.get('technique_id'),
    }

    def set_employee(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, []):
            self.pool.get('hr.technique').write(
                cr,
                uid,
                [record['technique_id'][0]],
                {
                    'cancellation_employee_send_ids': ((4, record['employee_id'][0]),),
                    'cancellation_employee_ids': ((0, 0, {'employee_id': record['employee_id'][0]}),),
                })
        return {'type': 'ir.actions.act_window_close'}


HrCommittee()