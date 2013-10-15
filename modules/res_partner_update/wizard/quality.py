# coding=utf-8
import numpy
from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel
from res_partner_update.partner_update import CRITERIAS

#CRITERIAS = ('terms_of_service', 'conformity', 'quality_feedback', 'completeness_of_reporting',)


class PartnerQualityControlWizard(TransientModel):
    _name = 'res.partner.quality.control.wizard'
    _rec_name = 'date_call'

    _columns = {
        'date_call': fields.datetime('Дата прозвона'),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'period_id': fields.many2one(
            'kpi.period',
            'Период',
            domain=[('calendar', '=', 'rus')]
        ),
    }

    _defaults = {
        'partner_id': lambda cr, u, i, c: c.get('partner_id'),
    }

    def set_quality(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            for service in record.partner_id.added_services_ids:
                specialist_id = 0
                launch_ids = self.pool.get('process.launch').search(cr, 1, [('partner_id', '=', record.partner_id.id), ('service_id', '=', service.service_id.id), ('state', 'in', ['in_process', 'finish'])])
                if launch_ids:
                    try:
                        launch = self.pool.get('process.launch').read(cr, 1, launch_ids[0], ['process_model', 'process_id'])
                        process = self.pool.get(launch['process.model']).read(cr, 1, launch['process_id'], ['specialist_id'])
                        specialist_id = process['specialist_id'][0]
                    except:
                        pass

                values = {
                    'period_id': record.period_id.id,
                    'partner_id': record.partner_id.id,
                    'date_call': record.date_call,
                    'service_id': service.service_id.id,
                    'specialist_id': specialist_id,
                    'criteria_ids': [(0, 0, {'name': x[0]}) for x in CRITERIAS]
                }
                self.pool.get('res.partner.quality.control').create(cr, uid, values)

        return {'type': 'ir.actions.act_window_close'}
PartnerQualityControlWizard()