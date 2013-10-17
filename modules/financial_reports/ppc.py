# coding=utf-8
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


STATES = (
    ('draft', 'Отчет сгенерирован'),
    ('head', 'Утвержден руководителем'),
    ('director', 'Утвержден функциональным директором'),
    ('finansist', 'Утвержден финансистом'),
)


class PPCReport(Model):
    _name = 'financial.reports.ppc'
    _description = u'Финансовые отчеты - PPC'

    def _line_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for data in self.read(cr, uid, ids, ['service_id', 'partner_id'], context):
            #for record in self.pool.get('brief.main').read(cr, 1, brief_ids, ['rep_file_id']):
            #    attach.extend([(0, 0, {'name': i.name, 'file': i.file, 'object': 'process.launch', 'user_id': i.user_id.id})
            #                   for i in self.pool.get('attach.files').browse(cr, 1, record['rep_file_id'])])
            res[data['id']] = 0
        return res

    _columns = {
        'start_date': fields.date('С'),
        'end_date': fields.date('По'),
        'state': fields.selection(STATES, string='Статус'),

        'history_ids': fields.one2many(
            'financial.history',
            'financial_id',
            'История',
            domain=[('financial_model', '=', _name)],
            context={'financial_model': _name}),

        'line_ids': fields.function(
            _line_ids,
            relation='financial.reports.ppc.line',
            type="one2many",
            string='Линии отчета',
            method=True,
            store=False,
            readonly=True),
    }
PPCReport()


class PPCReportLine(Model):
    _name = 'financial.reports.ppc.line'
    _description = u'Финансовые отчеты - PPC - Линия отчета'

    _columns = {
        'report_id': fields.many2one('financial.reports.ppc', 'Отчет PPC'),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'specialist_id': fields.many2one('res.users', 'Аккаунт-менеджер'),
        'paid_type': fields.selection(
            (
                ('cash', 'Оплата'),
                ('pre', 'Предоплата'),
                ('sur', 'Доплата'),
                ('post', 'Пост оплата'),
            ), 'Тип оплаты'
        ),
        'invoice_id': fields.many2one('account.invoice', 'Счет'),
        'service_id': fields.many2one('brief.services.stage', 'Услуга'),
        'pay_date': fields.date('Дата платежа'),
        'total': fields.float('Сумма платежа $'),
        'close_date': fields.char('Дата ЗД', size=50),
        'carry_over_revenue': fields.float('Переходящие доходы'),
        'discount_up': fields.float('Скидка Up в аккаунте'),
        'discount_partner': fields.float('Скидка Партнера'),
        'discount_nds': fields.float('НДС'),
        'co_costs_partner': fields.float('Переходящие затраты на партнера'),
        'costs_partner': fields.float('Затраты на Партнера'),
        'co_costs_employee': fields.float('Переходящие затраты на персонал'),
        'costs_employee': fields.float('Затраты на персонал'),
        'profit': fields.float('Валовая прибыль'),
    }
PPCReportLine()