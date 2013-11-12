# coding=utf-8
from openerp.osv.orm import TransientModel


class ReportQualityControlManager(TransientModel):
    _name = "report.quality.control.manager"
    _columns = {
        'manager_id'
        'service_count'
        'quality_point'
        'mbo'
        'quality_index'
    }

ReportQualityControlManager()