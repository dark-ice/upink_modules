# coding=utf-8
from openerp.osv import fields
from openerp.osv.orm import Model


class AccountInvoicePayLine(Model):
    _inherit = 'account.invoice.pay.line'

    def _get_specialist(self, cr, uid, ids, name, args, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['invoice_id', 'service_id'], context=context):
            invoice = self.pool.get('account.invoice').read(cr, 1, record['invoice_id'][0], ['partner_id'])
            launch_ids = self.pool.get('process.launch').search(cr, 1, [('partner_id', '=', invoice['partner_id'][0]), ('service_id', '=', record['service_id'][0])])
            for launch in self.pool.get('process.launch').read(cr, 1, launch_ids, ['process_id', 'process_model']):
                process = self.pool.get(launch['process_model']).read(cr, 1, launch['process_id'], ['specialist_id'])
                res[record['id']] = process['specialist_id'][0]
        return res

    _columns = {
        'specialist_id': fields.function(
            _get_specialist,
            type='many2one',
            relation='res.users',
            string='Аккаунт-менеджер'
        ),
        'close': fields.boolean('Закрыт счет?'),
        'close_date': fields.date('Дата закрытия'),
    }