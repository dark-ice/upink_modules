# -*- coding: utf-8 -*-
try:
    from collections import Counter
except ImportError:
    from res_partner_update.counter import Counter

from openerp.osv import fields
from openerp.osv.orm import TransientModel


class PartnerAddedServicesHistoryWizard(TransientModel):
    _name = 'partner.added.services.history.wizard'
    _columns = {
        'date_start': fields.date('Дата начала'),
        'date_finish': fields.date('Дата окончания'),
        'count_ids': fields.one2many('service.count.for.partner', 'count_id', 'количество услуг'),
        'count_service_ids': fields.one2many('service.name.for.partner', 'count_service_id', 'количество по услугам'),
        'count_direction_ids': fields.one2many('direction.name.for.partner', 'count_direction_id', 'количество по направлениям')
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = dict()
        for field in self._columns.keys():
            if field in context:
                res[field] = context[field]
        return res

    def get_report(self, cr, uid, ids, context=None):
        res_partner_pool = self.pool.get('res.partner')
        res_partner_service_history = self.pool.get('partner.added.services.history')
        service_start_ids = []
        service_finish_ids = []
        vals = dict()
        vals_list = list()

        for record in self.browse(cr, uid, ids, context):
            if record.date_start:
                service_start_ids = res_partner_service_history.search(cr, uid, [
                    ('date_start', '>', record.date_start), ('check_r', '=', True)
                ])

            if record.date_finish:
                service_finish_ids = res_partner_service_history.search(cr, uid, [
                    ('date_finish', '<', record.date_finish), ('check_r', '=', True)
                ])
            # получаю вхождения в оба листа в common
            common = list(set(service_start_ids) & set(service_finish_ids))

            partner_service_num = Counter([r['partner_id'][0] for r in res_partner_service_history.read(cr, 1, common, ['partner_id'])])
            sum_parnet = Counter(partner_service_num.values())

            service_partner_num = dict(set([(r['service_id'][0], r['partner_id'][0]) for r in res_partner_service_history.read(cr, 1, common, ['partner_id', 'service_id'])]))
            sum_parnet_service = Counter(service_partner_num.keys())

            direction_partner_num = dict(set([(r['direction'], r['partner_id'][0]) for r in res_partner_service_history.read(cr, 1, common, ['partner_id', 'direction'])]))
            sum_parnet_direction = Counter(direction_partner_num.keys())

            count_ids = [(0, 0, {'count_services': k, 'count_partners': sum_parnet[k]}) for k in sum_parnet.iterkeys()]
            count_service_ids = [(0, 0, {'service_id': k, 'count_partners': sum_parnet_service[k]}) for k in sum_parnet_service.iterkeys()]
            count_direction_ids = [(0, 0, {'direction_name': k, 'count_partners': sum_parnet_direction[k]}) for k in sum_parnet_direction.iterkeys()]

            action_pool = self.pool.get('ir.actions.act_window')
            action_id = action_pool.search(cr, uid, [('name', '=', 'Комплексный отчет по услугам')], context=context)
            if action_id:

                data = action_pool.read(cr, uid, action_id[0], context=context)
                data.update({
                    'nodestroy': True,
                    'context': {
                        'count_ids': count_ids,
                        'count_service_ids': count_service_ids,
                        'count_direction_ids': count_direction_ids,
                        'date_start': record.date_start,
                        'date_finish': record.date_finish,
                    }
                })

                return data

PartnerAddedServicesHistoryWizard()


class ServiceCountForPartner(TransientModel):
    _name = 'service.count.for.partner'
    _columns = {
        'count_id': fields.integer('ids отчета по количеству'),
        'count_services': fields.integer('Количество услуг'),
        'count_partners': fields.integer('Количество партнеров'),
    }

ServiceCountForPartner()


class ServiceNameForPartner(TransientModel):
    _name = 'service.name.for.partner'
    _columns = {
        'count_service_id': fields.integer('ids отчета по количестпу партнеров'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'count_partners': fields.integer('Количество партнеров'),
    }

ServiceNameForPartner()


class DirectionNameForPartner(TransientModel):
    _name = 'direction.name.for.partner'
    _columns = {
        'count_direction_id': fields.integer('ids отчета по количеству направлений'),
        'direction_name': fields.char('Направление', size=256),
        'count_partners': fields.integer('Количество партнеров'),
    }

DirectionNameForPartner()