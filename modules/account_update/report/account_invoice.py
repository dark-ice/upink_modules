# -*- coding: utf-8 -*-
from __future__ import print_function, division
import time
import math
from openerp.report import report_sxw
import pytils
import datetime
from pytils import dt


class AccountInvoiceDocument(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        self._cr = cr
        self._uid = 1
        super(AccountInvoiceDocument, self).__init__(cr, 1, name, context=context)
        self.localcontext.update({
            'time': time,
            'post': context.get('print', 'yes'),
            'get_client_info': self._get_client_info,
            'get_client_address': self._get_client_address,
            'get_post_client': self._get_post_client,
            'get_total': self._get_total,
            'get_word_cash': self._get_word,
            'get_date': self._get_date,
            'get_len': self._get_len,
        })

    @staticmethod
    def _get_total(cash, tax):
        t = tax / 100
        untax = round(cash / (1 + t), 2)
        tax_cash = cash - untax
        return untax, tax_cash

    @staticmethod
    def _get_word(cash):
        cash_d = math.modf(cash)
        if round(cash_d[0], 2) != 0.0:
            d = int(round(cash_d[0], 2) * 100)
            if d < 10:
                d = u"0%s" % d
            else:
                d = u"%s" % d
        else:
            d = u"00"
        d += u" коп"
        result = (pytils.numeral.rubles(cash_d[1]), d)
        return result

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

    def _get_client_address(self, data, address_type='ua'):
        bank = self.pool.get('res.partner.bank').read(self._cr, self._uid, data, ['type', 'address_ids', 'address_registration'])
        address_pool = self.pool.get('res.partner.bank.address')
        result = u""
        result_list = list()
        if bank['type'] == 'ur':
            address_ids = address_pool.search(self._cr, self._uid, [('name', '=', address_type), ('id', 'in', bank['address_ids'])])
            for item in address_pool.read(self._cr, self._uid, address_ids):
                if item['index']:
                    result_list.append(item['index'])
                if item['city']:
                    result_list.append(u"г. {city}".format(city=item['city']))
                if item['street']:
                    st = u'ул.'
                    if item['st_type'] == 'alleya':
                        st = u'Ал.'
                    if item['st_type'] == 'bulvar':
                        st = u'Бул.'
                    if item['st_type'] == 'naberegnaya':
                        st = u'Наб.'
                    if item['st_type'] == 'pereyloc':
                        st = u'Пр.'
                    if item['st_type'] == 'proezd':
                        st = u'Проезд.'
                    if item['st_type'] == 'prospect':
                        st = u'Просп.'
                    if item['st_type'] == 'ploshad':
                        st = u'Пл.'
                    result_list.append(u"{st_type} {street}".format(street=item['street'], st_type=st))
                if item['house']:
                    result_list.append(u"д. {house}".format(house=item['house']))
                if item['housing']:
                    result_list.append(u"корп. {housing}".format(housing=item['housing']))
                if item['building']:
                    result_list.append(u"стр. {building}".format(building=item['building']))
                if item['flat']:
                    ft = u'кв.'
                    if item['flat_type'] == 'room':
                        ft = u'ком.'
                    if item['flat_type'] == 'cabinet':
                        ft = u'каб.'
                    if item['flat_type'] == 'office':
                        ft = u'оф.'
                    if item['flat_type'] == 'sota':
                        ft = u'ячейка'
                    if item['flat_type'] == 'aya':
                        ft = u'а/я'
                    result_list.append(u"{flat_type} {flat}".format(flat_type=ft, flat=item['flat']))
                break

            if result_list:
                result = ', '.join(result_list)
        else:
            result = bank['address_registration']
        return result

    def _get_post_client(self, data):
        result_first = list()
        result_second = list()
        index = '-'

        for item in data:
            if item.name == 'mk':
                if item.street:
                    st = u'ул.'
                    if item['st_type'] == 'alleya':
                        st = u'Ал.'
                    if item['st_type'] == 'bulvar':
                        st = u'Бул.'
                    if item['st_type'] == 'naberegnaya':
                        st = u'Наб.'
                    if item['st_type'] == 'pereyloc':
                        st = u'Пр.'
                    if item['st_type'] == 'proezd':
                        st = u'Проезд.'
                    if item['st_type'] == 'prospect':
                        st = u'Просп.'
                    if item['st_type'] == 'ploshad':
                        st = u'Пл.'
                    result_first.append(u"{st_type} {street}".format(street=item.street, st_type=st))
                if item.house:
                    result_first.append(u"д. {house}".format(house=item.house))
                if item.housing:
                    result_first.append(u"корп. {housing}".format(housing=item.housing))
                if item.building:
                    result_first.append(u"ст. {building}".format(building=item.building))

                if item.index:
                    index = item.index
                if item.city:
                    result_second.append(u"г. {city}".format(city=item.city))
                if item.flat:
                    ft = u'кв.'
                    if item.flat_type == 'room':
                        ft = u'ком.'
                    if item.flat_type == 'cabinet':
                        ft = u'каб.'
                    if item.flat_type == 'office':
                        ft = u'оф.'
                    if item.flat_type == 'sota':
                        ft = u'ячейка'
                    if item.flat_type == 'aya':
                        ft = u'а/я'
                    result_second.append(u"{flat_type} {flat}".format(flat_type=ft, flat=item.flat))

                break

        return ', '.join(result_first), ', '.join(result_second), index

    def _get_client_info(self, data):
        bank = self.pool.get('res.partner.bank').browse(self._cr, self._uid, data)
        result_list = list()

        if bank.inn:
            result_list.append(u"ИНН {0}".format(bank.inn))
        if bank.kpp:
            result_list.append(u"КПП {0}".format(bank.kpp))
        address = self._get_client_address(data)
        if address:
            result_list.append(address)

        if result_list:
            return ', '.join(result_list)

    @staticmethod
    def _get_date(date):
        date_list = str(date).split('/')
        d = datetime.date(int(date_list[2]), int(date_list[1]), int(date_list[0]))
        result = dt.ru_strftime(u"%d %B %Y", d, inflected=True)
        return result

    @staticmethod
    def _get_len(date):
        if isinstance(date, (list, tuple)):
            return len(date)
        else:
            return 0


report_sxw.report_sxw(
    'report.account.completion.ru',
    'account.invoice.documents',
    'addons/account_update/report/completion_ru.mako',
    parser=AccountInvoiceDocument
)

report_sxw.report_sxw(
    'report.account.completion.ua',
    'account.invoice.documents',
    'addons/account_update/report/completion_ua.mako',
    parser=AccountInvoiceDocument
)

report_sxw.report_sxw(
    'report.account.payment.ru',
    'account.invoice',
    'addons/account_update/report/payment_ru.mako',
    parser=AccountInvoiceDocument
)

report_sxw.report_sxw(
    'report.account.payment.ua',
    'account.invoice',
    'addons/account_update/report/payment_ua.mako',
    parser=AccountInvoiceDocument
)

report_sxw.report_sxw(
    'report.invoice.ru',
    'account.invoice.documents',
    'addons/account_update/report/invoice.mako',
    parser=AccountInvoiceDocument
)

report_sxw.report_sxw(
    'report.post',
    'account.invoice',
    'addons/account_update/report/postman.mako',
    parser=AccountInvoiceDocument
)