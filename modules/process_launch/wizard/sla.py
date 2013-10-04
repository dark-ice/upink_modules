# coding=utf-8
__author__ = 'andrey'
from datetime import date
import numpy
from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel


class ProcessSlaWizard(TransientModel):
    _name = 'process.sla.wizard'
    _inherit = 'process.sla'

    def get_default_period(self, cr, uid, context=None):
        if context is not None:
            period_pool = self.pool.get('kpi.period')
            sla_ids = self.pool.get('process.sla').search(
                cr,
                uid,
                [
                    ('process_model', '=', context.get('process_model')),
                    ('process_id', '=', context.get('process_id'))
                ])

            if sla_ids:
                sla = self.pool.get('process.sla').read(cr, uid, sla_ids[0], ['period_id'])
                next_period = period_pool.next(cr, sla['period_id'][0])
                period_id = next_period.id
            else:
                period = period_pool.get_by_date(cr, date.today(), 'rus')
                period_id = period.id
            return period_id

        return False

    def change_period(self, cr, uid, ids, process_model, process_id, period_id, context=None):
        value = {}
        period_pool = self.pool.get('kpi.period')
        sla_pool = self.pool.get('process.sla')
        s_ids = sla_pool.search(
            cr,
            uid,
            [
                ('process_model', '=', process_model),
                ('process_id', '=', process_id),
                ('period_id', '=', period_id)])
        if s_ids:
            raise osv.except_osv("Error", "Вы не можете создать более 1го SLA на определенный месяц!")
        else:
            period = period_pool.browse(cr, uid, period_id, context)
            prev_sla_ids = sla_pool.search(
                cr,
                uid,
                [
                    ('process_model', '=', process_model),
                    ('process_id', '=', process_id),
                    ('period_id.name', '<', period.name)
                ]
            )
            sla_obj = None
            prev = False
            if prev_sla_ids:
                sla_obj = sla_pool.browse(cr, uid, prev_sla_ids[0])
                prev = True
            else:
                sla_ids = sla_pool.search(
                    cr,
                    uid,
                    [
                        ('process_model', '=', process_model),
                        ('process_id', '=', process_id)
                    ])
                if sla_ids:
                    sla_obj = sla_pool.browse(cr, uid, sla_ids[0])
            if sla_obj:
                sla = [(0, 0,
                        {
                            'name': i.name.id,
                            'units': i.units,
                            'weight': i.weight,
                            'previous_period': i.fact if prev else 0.0
                        }) for i in sla_obj.line_ids]
                if sla:
                    value.update({'line_ids': sla})
        return {'value': value}

    _columns = {
        'process_id': fields.integer('Process ID', readonly=False, invisible=True),
        'process_model': fields.char('Process Model', size=64, readonly=False, invisible=True),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')], required=True),
        'line_ids': fields.one2many('process.sla.line.wizard', 'sla_id', 'Показатели'),
        'write': fields.boolean('Сохраняем?'),
        'sla_id': fields.integer('Sla id')
    }

    _defaults = {
        'write': lambda cr, u, i, ctx: ctx.get('write'),
        'sla_id': lambda cr, u, i, ctx: ctx.get('sla_id'),
        'process_model': lambda cr, u, i, ctx: ctx.get('process_model'),
        'process_id': lambda cr, u, i, ctx: ctx.get('process_id'),
        'period_id': lambda s, c, u, ctx: s.get_default_period(c, u, ctx),
    }

    def set_sla(self, cr, uid, ids, context=None):
        sla_pool = self.pool.get('process.sla')

        for record in self.browse(cr, uid, ids, context):

            if record.write:
                values = {
                    'line_ids': [(6, 0,
                                  {
                                      'name': i.name.id,
                                      'units': i.units,
                                      'weight': i.weight,
                                      'fact': i.fact
                                  }) for i in record.line_ids],
                    'avg_mbo': numpy.mean([i.mbo for i in record.line_ids]) or 0.0
                }

            else:
                values = {
                    'process_model': record.process_model,
                    'process_id': record.process_id,
                    'period_id': record.period_id.id,
                    'type': record.type,
                    'line_ids': [(0, 0,
                                  {
                                      'name': i.name.id,
                                      'units': i.units,
                                      'weight': i.weight,
                                      'fact': i.fact
                                  }) for i in record.line_ids],
                    'avg_mbo': numpy.mean([i.mbo for i in record.line_ids]) or 0.0
                }
                sla_pool.create(cr, 1, values)
        return {'type': 'ir.actions.act_window_close'}
ProcessSlaWizard()


class ProcessSlaLineWizard(TransientModel):
    _name = 'process.sla.line.wizard'
    _inherit = 'process.sla.line'
ProcessSlaLineWizard()