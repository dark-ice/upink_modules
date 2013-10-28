# -*- coding: utf-8 -*-
from __future__ import print_function, division
import time
import math
from openerp.report import report_sxw
import pytils
from datetime import datetime
from pytils import dt


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        self._cr = cr
        self._uid = 1
        super(Parser, self).__init__(cr, 1, name, context=context)
        self.localcontext.update({
            'time': time,
            'post': context.get('print', 'yes'),
            'get_client_info': self._get_client_info,
            'get_client_address': self._get_client_address,
            'get_total': self._get_total,
            'get_word_cash': self._get_word,
            'get_date': self._get_date,
            'get_len': self._get_len,
            'get_getter': self.get_getter,
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

    def _get_client_address(self, data):
        bank = self.pool.get('res.partner.bank').browse(self._cr, self._uid, data)
        result = u""
        result_list = list()
        if bank.type == 'ur':
            ur_address = [item for item in bank.address_ids if item.name == 'ua']
            if ur_address:
                address = ur_address[0]
                index = self.get_str(address.index)
                city = self.get_str(address.city)
                street = self.get_str(address.street)
                house = self.get_str(address.house)

                if address.index:
                    result_list.append(address.index)
                if address.city:
                    result_list.append(address.city)
                if address.street:
                    result_list.append(address.street)
                if address.house:
                    result_list.append(address.house)

            if result_list:
                result = ', '.join(result_list)
        else:
            result = bank.address_registration
        return result

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
        pattern = '%Y-%m-%d'
        if '/' in date:
            #date_list = str(date).split('/')
            #d = datetime.date(int(date_list[2]), int(date_list[1]), int(date_list[0]))
            #d = datetime.strptime(str(date), '%d/%m/%Y')
            pattern = '%d/%m/%Y'
        #elif '-' in date:
            #date_list = str(date).split('-')
            #d = datetime.date(int(date_list[0]), int(date_list[1]), int(date_list[2]))

        d = datetime.strptime(str(date), pattern)
        result = dt.ru_strftime(u"%d %B %Y", d, inflected=True)
        return result

    @staticmethod
    def _get_len(date):
        if isinstance(date, (list, tuple)):
            return len(date)
        else:
            return 0

    @staticmethod
    def get_getter(pay_ids):
        return u', '.join([item.getter for item in pay_ids])