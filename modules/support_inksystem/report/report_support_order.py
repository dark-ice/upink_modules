# -*- coding: utf-8 -*-
from __future__ import print_function
import time
from report import report_sxw
from osv import osv
import pooler


class support_order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(support_order, self).__init__(cr, 1, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_type': self._get_type,
        })

    def _get_type(self, data):
        if data == 'warranty':
            return 'гарантийный'
        return 'не гарантийный'

report_sxw.report_sxw(
    'report.support_order_ru',
    'supp.sale',
    'support_inksystem/report/support_order_ru.rml',
    parser=support_order
)

report_sxw.report_sxw(
    'report.support_order_pl',
    'supp.sale',
    'support_inksystem/report/support_order_pl.rml',
    parser=support_order
)
