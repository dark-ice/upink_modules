# coding=utf-8
from operator import add
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel


class CdDispositionAgreementWizard(TransientModel):
    _name = 'cd.disposition.agreement.wizard'
    _description = u'Распоряжения - Согласование Wizard'

    _columns = {
        'group_id': fields.many2one('storage.groups', string='Группа', domain=[('id', 'in', [111, 22])]),
        'user_id': fields.many2one('res.users', string='Сотрудник'),
        'disposition_id': fields.many2one('cd.disposition', 'Распоряжение'),
    }

    _defaults = {
        'disposition_id': lambda cr, u, i, ctx: ctx.get('disposition_id'),
    }

    def set_employee(self, cr, uid, ids, context=None):
        pool = self.pool.get('cd.disposition')
        group_pool = self.pool.get('storage.groups')
        for record in self.read(cr, uid, ids, []):
            vals = {}
            disposition = pool.read(cr, 1, record['disposition_id'][0], ['agreement_user_ids', 'agreement_group_ids'])
            gr_users = [x['users_group'] or [] for x in group_pool.read(cr, 1, disposition['agreement_group_ids'] or [], ['users_group'])] or []
            if gr_users:
                gr_users = reduce(add, gr_users)
            users = disposition['agreement_user_ids'] or [] + gr_users

            new_users = []
            if record['user_id']:
                new_users.append(record['user_id'][0])
            if record['group_id']:
                new_users += group_pool.read(cr, 1, record['group_id'][0], ['users_group'])['users_group']
                vals['agreement_group_ids'] = [(4, record['group_id'][0])]

            usrs = list(set(new_users).difference(set(users)))
            vals.update({
                'agreement_user_ids': [(4, x) for x in usrs],
                'agreement_ids': [(0, 0, {'user_id': x}) for x in usrs],
            })
            pool.write(cr, uid, [record['disposition_id'][0]], vals)
        return {'type': 'ir.actions.act_window_close'}


CdDispositionAgreementWizard()