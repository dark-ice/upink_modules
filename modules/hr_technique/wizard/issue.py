# coding=utf-8
import datetime
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel


class Issue(TransientModel):
    _name = 'hr.technique.issue'
    _description = u'Учет техники - Выдача'

    _columns = {
        'technique_id': fields.many2one('hr.technique', 'Техника'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', required=True),
        'state': fields.char('Статус', size=256),
    }

    _defaults = {
        'technique_id': lambda cr, u, i, ctx: ctx.get('technique_id'),
        'state': lambda cr, u, i, ctx: ctx.get('state'),
    }

    def set_issue(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, []):
            self.pool.get('hr.technique').write(cr, uid, [record['technique_id'][0]], {'state': record['state'], 'employee_id': record['employee_id'][0], 'date_of_issue': datetime.date.today().strftime("%d/%m/%y")})
        return {'type': 'ir.actions.act_window_close'}

Issue()