# -*- encoding: utf-8 -*-
from osv import fields, osv


class indicators_sla_stage(osv.osv):
    _name = "indicators.sla.stage"
    _description = u"Справочник SLA показателей"

    _columns = {
        'name': fields.char('Показатель', size=156, required=True, select=True),
        'type': fields.selection(
            [
                ('project', 'SLA проекта'),
                ('agent', 'SLA агента'),
            ], 'Тип показателя', select=True),
        'compan_type': fields.selection(
            [
                ('incoming', 'входящая компания'),
                ('outgoing', 'исходящая компания'),
            ], 'Тип компании', select=True),
        'strategy_type': fields.selection(
            [
                ('start', 'запуск стратегии'),
                ('implementation', 'реализация стратегии'),
            ], 'Процесс стратегии', select=True),
        'model': fields.selection(
            [
                ('outsourcing_contact_centr', 'Аутсорсинговый контакт центр'),
                ('ppc_company', 'Запуск и реализация компании PPC'),
                ('seo_strategy', 'Разработка и реализация стратегии SEO'),
                ('smm_strategy', 'Реализация стратегии SMM'),
            ], 'Модуль', required=True),
        'formula': fields.text('Формула', required=True),
    }

indicators_sla_stage()


class sla_interval_date(osv.osv):
    _name = "sla.interval.date"
    _description = u"Справочник SLA переиодов"
    _columns = {
        'name': fields.char('Месяц/Год', size=64, select=True),
    }
    _sql_constraints = [('name', 'unique(name)', u'Такой период уже есть!')]
sla_interval_date()
