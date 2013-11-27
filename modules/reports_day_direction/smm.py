# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model

class ReportDaySmmStatisticPlan(Model):
    _name = "report.day.smm.static.plan"
    _description = u"доп модель отчета по направлению smm"
    _columns = {
        'process_smm_id': fields.many2one('process.call.in', 'Проект', domain="[('state', '=', 'development')]"),

    }

ReportDaySmmStatisticPlan()