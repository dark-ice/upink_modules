# coding=utf-8
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp.osv import fields
from openerp.osv.orm import Model


def get_last_work_day(source_date):
    month = source_date.month
    year = source_date.year

    day_in_month = calendar.monthrange(year, month)[1]
    new_date = date(year, month, day_in_month)
    if new_date.weekday() in (0, 1, 2, 3, 4):
        return new_date
    else:
        return new_date - relativedelta(days=new_date.weekday()-4)


class AccountInvoicePayLine(Model):
    _inherit = 'account.invoice.pay.line'

    def _get_specialist(self, cr, uid, ids, name, args, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['invoice_id', 'service_id'], context=context):
            res[record['id']] = False
            if record['invoice_id']:
                invoice = self.pool.get('account.invoice').read(cr, 1, record['invoice_id'][0], ['partner_id'])
                if record['service_id'] and invoice['partner_id']:
                    launch_ids = self.pool.get('process.launch').search(cr, 1, [('partner_id', '=', invoice['partner_id'][0]), ('service_id', '=', record['service_id'][0])])
                    for launch in self.pool.get('process.launch').read(cr, 1, launch_ids, ['process_id', 'process_model']):
                        if launch['process_model'] and launch['process_id']:
                            process = self.pool.get(launch['process_model']).read(cr, 1, launch['process_id'], ['specialist_id'])
                            if process.get('specialist_id'):
                                res[record['id']] = process['specialist_id'][0]
        return res

    def onchange_close(self, cr, uid, ids, close):
        if close:
            source_date = date.today()
            current_day = source_date.day
            if current_day < 20:
                source_date = date.today() - relativedelta(months=1)

            return {'value': {'close_date': get_last_work_day(source_date).strftime('%Y-%m-%d')}}
        else:
            return {'value': {'close_date': False}}

    _columns = {
        'specialist_id': fields.function(
            _get_specialist,
            type='many2one',
            relation='res.users',
            string='Аккаунт-менеджер',
            store=True
        ),
        'close': fields.boolean('Закрыт счет?'),
        'close_date': fields.date('Дата закрытия'),
        'invoice_date': fields.related(
            'invoice_id',
            'date_invoice',
            type='date',
            string='Дата платежа',
            store=True,
        ),
        'paid_type': fields.selection(
            (
                ('cash', 'Оплата'),
                ('pre', 'Предоплата'),
                ('sur', 'Доплата'),
                ('post', 'Пост оплата'),
            ), 'Тип оплаты'
        ),
    }

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('report'):
            order = 'partner_id ASC, service_id ASC, invoice_date ASC'
        return super(AccountInvoicePayLine, self).search(cr, user, args, offset, limit, order, context, count)
AccountInvoicePayLine()