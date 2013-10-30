# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from datetime import datetime
from openerp.osv.orm import TransientModel
import pytz


class InvoiceDocumentWizard(TransientModel):
    _name = 'account.invoice.document.wizard'

    _columns = {
        'document_line_id': fields.one2many('account.invoice.document.line.wizard', 'wzr_id', u'Справочник'),
        'name': fields.selection(
            (
                ('completion_ru', u'Акт выполненных работ Россия'),
                ('completion_ua', u'Акт выполненных работ Украина'),
                ('facture_ru', u'Счет фактура Россия'),
                ('facture_ua', u'Счет фактура Украина'),
                ('payment_ru', u'Счет на оплату Россия'),
            ), u'Тип документа', invisible=True
        ),
        'document_date': fields.date(u'Дата в документе'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', invisible=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        line_pool = self.pool.get('account.invoice.line')
        document_pool = self.pool.get('account.invoice.documents')
        if context is None:
            context = {}
        res = dict()
        for field in self._columns.keys():
            if field in context:
                res[field] = context[field]

        plist = list()
        for p in line_pool.browse(cr, uid, line_pool.search(cr, uid, [('invoice_id', '=', context['invoice_id'])])):
            document_line_ids = document_pool.search(cr, uid, [('invoice_id', '=', context['invoice_id']),
                                                               ('name', '=', context['name'])])
            total = sum([x.document_cash for x in document_pool.browse(cr, uid, document_line_ids)]) or 0.0
            vals = dict()
            vals['service_id'] = p.service_id.id
            vals['name'] = p.price_currency - total
            plist.append((0, 0, vals))
        res['document_line_id'] = plist

        res['document_date'] = datetime.today().strftime("%Y-%m-%d")
        return res

    def set_pay(self, cr, uid, ids, context=None):
        document_pool = self.pool.get('account.invoice.documents')
        document_line_pool = self.pool.get('account.invoice.document.line')
        for record in self.browse(cr, uid, ids, context):
            self.pool.get('account.invoice').write(cr, uid, [record.invoice_id.id], {
                'close_doc_create': record.document_date})
            total = sum([item.name for item in record.document_line_id])
            if round(total, 2) > round(record.invoice_id.a_total, 2):
                raise osv.except_osv('Warning!', 'Сумма платежа не может быть больше чем сумма счета')
            document_id = document_pool.create(cr, uid, {
                'name': record.name,
                'document_date': record.document_date,
                'document_cash': total,
                'invoice_id': record.invoice_id.id
            })
            for item in record.document_line_id:
                document_line_pool.create(cr, uid, {
                    'document_id': document_id,
                    'service_id': item.service_id.id,
                    'name': item.name
                })
        return {'type': 'ir.actions.act_window_close'}


InvoiceDocumentWizard()


class InvoiceDocumentLineWizard(TransientModel):
    _name = 'account.invoice.document.line.wizard'

    _columns = {
        'service_id': fields.many2one('brief.services.stage', u'Услуга'),
        'name': fields.float(u'Сумма к оплате', digits=(10, 2)),
        'wzr_id': fields.many2one('account.invoice.document.wizard', 'Wizard Pay'),
    }


InvoiceDocumentLineWizard()