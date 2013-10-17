# coding=utf-8
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model


class FinancialHistory(Model):
    _name = 'financial.history'
    _description = u'Финансовые отчеты - История'

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'state': fields.char('На этап', size=65),
        'financial_id': fields.integer('Process ID', readonly=True),
        'financial_model': fields.char('Process Model', size=64, readonly=True, change_default=True),
    }

    _defaults = {
        'financial_model': lambda cr, u, i, ctx: ctx.get('financial_model'),
    }

    _order = "create_date desc"
FinancialHistory()