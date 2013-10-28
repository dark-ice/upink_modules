# -*- coding: utf-8 -*-
import math
from openerp.report import report_sxw
import pytils


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        self._cr = cr
        self._uid = 1
        super(Parser, self).__init__(cr, 1, name, context=context)
