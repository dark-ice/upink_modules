# -*- coding: utf-8 -*-
from datetime import datetime
import pytz

try:
    from collections import Counter
except ImportError:
    from res_partner_update.counter import Counter

from openerp.osv import fields
from openerp.osv.orm import TransientModel


class PartnerAddedServicesHistoryWizard(TransientModel):
    _name = 'partner.added.services.history.wizard'
    _columns = {
        'date_start': fields.date('Дата начала', required=1),
        'date_finish': fields.date('Дата окончания', required=1),
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
        res['date_finish'] = datetime.now(pytz.utc).strftime('%Y-%m-%d')
        return res

    def get_report(self, cr, uid, ids, context=None):
        res_partner_service_history = self.pool.get('partner.added.services.history')

        for record in self.browse(cr, uid, ids, context):
            common = res_partner_service_history.search(cr, uid, [
                    ('date_start', '>', record.date_start), ('date_start', '<', record.date_finish), ('check_r', '=', True)
                ])

            partners = res_partner_service_history.read(cr, 1, common, ['partner_id', 'service_id', 'direction'])
            partner_service_num = Counter([r['partner_id'][0] for r in partners])
            sum_parnet = Counter(partner_service_num.values())

            service_partner_num = [x[0] for x in set([(r['service_id'][0], r['partner_id'][0]) for r in partners])]
            sum_parnet_service = Counter(service_partner_num).most_common()

            direction_partner_num = [x[0] for x in set([(r['direction'], r['partner_id'][0]) for r in partners])]
            sum_parnet_direction = Counter(direction_partner_num).most_common()

            count_ids = [(0, 0, {'count_services': k, 'count_partners': sum_parnet[k]}) for k in sum_parnet.iterkeys()]
            count_service_ids = [(0, 0, {'service_id': k[0], 'count_partners': k[1]}) for k in sum_parnet_service]
            count_direction_ids = [(0, 0, {'direction_name': k[0], 'count_partners': k[1]}) for k in sum_parnet_direction]

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