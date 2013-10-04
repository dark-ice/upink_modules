# -*- coding: utf-8 -*-
import math
from openerp.report import report_sxw
import pytils


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        self._cr = cr
        self._uid = 1
        super(Parser, self).__init__(cr, 1, name, context=context)
        ids = context.get('ids', [])
        model = context.get('model', [])
        new_objects = []
        tm_objects = []
        if model:
            for record in self.pool.get(context['model']).browse(cr, uid, ids):
                if len(tm_objects) < 3:
                    tm_objects.append(record)
                else:
                    new_objects.append(tm_objects)
                    tm_objects = [record, ]
            new_objects.append(tm_objects)

        self.localcontext.update({
            'new_objects': new_objects,
            'new_row': self.new_row,
            'new_row_mp': self.new_row_mp,
            'sum_row': self.sum_row,
            'sum_row_mp': self.sum_row_mp,
            'sum_all': self.sum_all,
            'sum_all_mp': self.sum_all_mp,
            'check_cnt': self.check_cnt,
            's_indx': self.s_indx,
            'is_obj': self.is_obj,
            'incoming': self.incoming,
        })

    @staticmethod
    def get_str(value):
        if value:
            try:
                unicode(value, "ascii")
            except UnicodeError:
                value = unicode(value, "utf-8")
            except TypeError:
                pass
            else:
                # value was valid ASCII data
                pass
            return value

    def new_row(self, week_number, date):
        if self.pool.get('day.report.planning').search(self._cr, self._uid, [('week_number', '=', week_number), ('date', '>', date)]):
            return False
        return True

    def sum_row(self, week_number, field):
        s = 0
        row_ids = self.pool.get('day.report.planning').search(self._cr, self._uid, [('week_number', '=', week_number), ])
        for k in self.pool.get('day.report.planning').read(self._cr, self._uid, row_ids, [field]):
            s += k[field]
        return s

    def sum_all(self, field):
        s = 0
        row_ids = self.pool.get('day.report.planning').search(self._cr, self._uid, [])
        for k in self.pool.get('day.report.planning').read(self._cr, self._uid, row_ids, [field]):
            s += k[field]
        return s

    def new_row_mp(self, week_number, date):
        if self.pool.get('day.report.mp').search(self._cr, self._uid, [('week_number', '=', week_number), ('date', '>', date)]):
            return False
        return True

    def sum_row_mp(self, week_number, field):
        s = 0
        row_ids = self.pool.get('day.report.mp').search(self._cr, self._uid, [('week_number', '=', week_number), ])
        for k in self.pool.get('day.report.mp').read(self._cr, self._uid, row_ids, [field]):
            s += k[field]
        return s

    def sum_all_mp(self, field):
        s = 0
        row_ids = self.pool.get('day.report.mp').search(self._cr, self._uid, [])
        for k in self.pool.get('day.report.mp').read(self._cr, self._uid, row_ids, [field]):
            s += k[field]
        return s

    def check_cnt(self, indx, i, lens):
        if indx + i < lens:
            return True
        return False

    def s_indx(self, indx, i):
        return indx+i

    def is_obj(self, obj, i):
        try:
            if obj[i]:
                return True
            return False
        except:
            return False

    def incoming(self, week_number, date):
        ids = self.pool.get('day.report.planning').search(self._cr, self._uid, [('week_number','=', week_number), ('date', '<=', date)])
        result = sum(r['plan_total'] for r in self.pool.get('day.report.planning').read(self._cr, self._uid, ids, ['plan_total']))
        return result


