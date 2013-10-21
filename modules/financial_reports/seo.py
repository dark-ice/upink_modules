# coding=utf-8
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model


class ReportSeo(Model):
    _name = 'financial.report.seo'
    _description = u'Финансовые отчеты - SEO'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for record_id in ids:
            access = str()

            #  Руководитель PPC (Чуб Юля)
            if uid == 96:
                access += 'h'

            #  Функциональный директор (Чабанов Кирилл)
            if uid == 472:
                access += 'd'

            #  Финансист (Овчарова Таня)
            if uid == 170:
                access += 'f'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[record_id] = val
        return res

    _columns = {
        'start_date': fields.date(
            'С',
            readonly=True,
            states={
                'draft': [('readonly', False)]
            }
        ),
        'end_date': fields.date(
            'По',
            readonly=True,
            states={
                'draft': [('readonly', False)]
            }
        ),
        'state': fields.selection(STATES, string='Статус', readonly=True,),
        'history_ids': fields.one2many(
            'financial.history',
            'financial_id',
            'История',
            readonly=True,
            domain=[('financial_model', '=', _name)],
            context={'financial_model': _name}),
        'check_h': fields.function(
            _check_access,
            method=True,
            string='Проверка на руководителя PPC',
            type='boolean',
            invisible=True
        ),
        'check_d': fields.function(
            _check_access,
            method=True,
            string='Проверка на функционального директора',
            type='boolean',
            invisible=True
        ),
        'check_f': fields.function(
            _check_access,
            method=True,
            string='Проверка на финансиста',
            type='boolean',
            invisible=True
        ),
    }

    _defaults = {
        'state': 'draft',
        'check_h': lambda s, c, u, cnt: u == 96 or u == 1,
    }
ReportSeo()