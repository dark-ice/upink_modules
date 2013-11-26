# coding=utf-8
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model


class ReportDayPPC(Model):
    _name = 'report.day.ppc'
    _description = u'Ежедневный отчет направлений - PPC'

    _columns = {
    }


ReportDayPPC()