# coding=utf-8
from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel

__author__ = 'skripnik'


class PartnerAddedServicesWizard(TransientModel):
    _name = 'partner.added.services.wizard'
    _columns = {
        'date': fields.date('дата'),
        'type': fields.char('тип даты', size=20),
        'partner_id': fields.integer('партнер'),
        'service_id': fields.integer('сервисы'),
        'comment': fields.text('комментарий'),
        'budget': fields.float('бюджет'),
        'active_id': fields.integer('Active ID'),
        # 'history_id': fields.integer('History ID')
    }

    _defaults = {
        'type': lambda c, u, i, cntx: cntx.get('type'),
        'budget': lambda c, u, i, cntx: cntx.get('budget'),
        'comment': lambda c, u, i, cntx: cntx.get('comment'),
        'service_id': lambda c, u, i, cntx: cntx.get('service_id'),
        'partner_id': lambda c, u, i, cntx: cntx.get('partner_id'),
        # 'history_id': lambda c, u, i, cntx: cntx.get('history_id'),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        defaults = super(PartnerAddedServicesWizard, self).default_get(cr, uid, fields_list, context)
        defaults['active_id'] = context.get('active_id')
        return defaults

    def set_service(self, cr, uid, ids, context=None):
        service_pool = self.pool.get('partner.added.services')
        for wizard in self.read(cr, uid, ids, []):

            history_id = 0
            date_st = service_pool.read(cr, uid, wizard['active_id'], ['date_start', 'history_ids'])
            if date_st['date_start'] > wizard['date']:
                raise osv.except_osv('Отключение услуги', 'Дата окончания не может быть меньше даты начала')
            if date_st['history_ids']:
                history_id = date_st['history_ids'][-1]
            if history_id != 0:
                history = self.pool.get('partner.added.services.history').read(cr, 1, history_id, ['date_start', 'date_finish', 'service_id'])
            if history['date_start'] == date_st['date_start']:
                lines = [(1, history_id, {'date_finish': wizard['date'], 'budget': wizard['budget'], 'comment': wizard['comment']})]
            else:
                if not history['date_finish']:
                    raise osv.except_osv('Незакрытая услуга', 'Пожалуйста, закройте предидущий период по этой услуге!')
                lines = [(0, 0, {
                    'date_finish': wizard['date'],
                    'date_start': date_st['date_start'],
                    'budget': wizard['budget'],
                    'comment': wizard['comment'],
                    'partner_id': wizard['partner_id'],
                    'service_id': wizard['service_id']
                })]
            service_pool.write(
                cr,
                uid,
                [wizard['active_id']],
                {
                    'check': False,
                    'date_finish': wizard['date'],
                    'history_ids': lines
                },
                context=None)

            invoice_ids = self.pool.get('account.invoice').search(cr, 1, [
                ('partner_id', '=',  wizard['partner_id']),
                ('date_invoice', '>', wizard['date']),
                ('invoice_line.service_id', '=', wizard['service_id'])
            ])
            if invoice_ids:
                invoice = self.pool.get('account.invoice').read(cr, invoice_ids[0], ['date_invoice'])
                service_pool.connect_service(cr, wizard['partner_id'], wizard['service_id'], invoice['date_start'])
        return {'type': 'ir.actions.act_window_close'}

PartnerAddedServicesWizard()