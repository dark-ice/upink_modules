# coding=utf-8
from openerp.osv import fields
from openerp.osv.orm import TransientModel


class ReportQualityControlManager(TransientModel):
    _name = "report.quality.control.manager"
    _columns = {
        'manager_id': fields.many2one('res.users', 'Менеджер'),
        'service_count': fields.integer('Количество оцененнызх услуг'),
        'quality_point': fields.integer('Уровень удовлетворенности'),
        'mbo': fields.integer('MBO по услуге'),
        'quality_index': fields.integer('Индекс удевлетвореннносте'),
        'date_start': fields.date('Дата начала'),
        'date_finish': fields.date('Дата окончания'),
    }

ReportQualityControlManager()