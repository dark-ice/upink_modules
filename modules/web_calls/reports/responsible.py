# coding=utf-8
from datetime import datetime, timedelta
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model
from .. import calls

__author__ = 'andrey'


class ResponsibleCalls(Model):
    _name = "web.calls.responsible.report"
    _description = u"Отчет по менеджерам"
    _auto = False

    _columns = {
        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),

        'call_date': fields.date('Дата звонка'),
        
        'responsible_id': fields.many2one('res.users', 'Менеджер'),

        'kiev': fields.integer('Киев'),
        'kharkov': fields.integer('Харьков'),
        'lvov': fields.integer('Львов'),
        'moscow': fields.integer('Москва'),
        'volgograd': fields.integer('Волгоград'),
        'novosibirsk': fields.integer('Новосибирск'),
        'saintpetersburg': fields.integer('Санкт-Петербург'),
        'ekaterinburg': fields.integer('Екатеринбург'),
        'almaty': fields.integer('Алматы'),
        'rostovondon': fields.integer('Ростов на Дону'),
        'kazan': fields.integer('Казань'),
        'chelyabinsk': fields.integer('Челябинск'),
        'nizhnynovgorod': fields.integer('Нижний Новгород'),
        'samara': fields.integer('Самара'),
        'irkutsk': fields.integer('Иркутск'),
        'voronezh': fields.integer('Воронеж'),
        'perm': fields.integer('Пермь'),
        'saratov': fields.integer('Саратов'),
        'krasnodar': fields.integer('Краснодар'),
        'warsaw': fields.integer('Варшава'),
        'omsk': fields.integer('Омск'),
        'odessa': fields.integer('Одесса'),
        'dnepropetrovsk': fields.integer('Днепропетровск'),
        'donetsk': fields.integer('Донецк'),
        'minsk': fields.integer('Минск'),
        'astana': fields.integer('Астана'),

        'livesite': fields.integer('Продажи с Живосайта'),
        'adminpanel': fields.integer('Продажи с Админпанели'),
        'shara': fields.integer('Халява'),
        'total': fields.integer('Всего'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'web_calls_responsible_report')
        cr.execute("""
            create or replace view web_calls_responsible_report as (
                SELECT
                    row_number() over() as id,
                    to_char(NOW(), 'YYYY-MM-DD') date_end,
                    to_char(NOW(), 'YYYY-MM-DD') date_start,
                    concat(extract(YEAR FROM call_date), '-', extract(MONTH FROM call_date), '-', extract(DAY FROM call_date))::date call_date,
                    responsible_id,

                    sum(case when region='kiev' then 1 else 0 end) kiev,
                    sum(case when region='kharkov' then 1 else 0 end) kharkov,
                    sum(case when region='lvov' then 1 else 0 end) lvov,
                    sum(case when region='msk' then 1 else 0 end) moscow,
                    sum(case when region='volgograd' then 1 else 0 end) volgograd,
                    sum(case when region='novosibirsk' then 1 else 0 end) novosibirsk,
                    sum(case when region='spb' then 1 else 0 end) saintpetersburg,
                    sum(case when region='ekb' then 1 else 0 end) ekaterinburg,
                    sum(case when region='alm' then 1 else 0 end) almaty,
                    sum(case when region='rostov' then 1 else 0 end) rostovondon,
                    sum(case when region='kazan' then 1 else 0 end) kazan,
                    sum(case when region='chelyabinsk' then 1 else 0 end) chelyabinsk,
                    sum(case when region='nino' then 1 else 0 end) nizhnynovgorod,
                    sum(case when region='samara' then 1 else 0 end) samara,
                    sum(case when region='irkutsk' then 1 else 0 end) irkutsk,
                    sum(case when region='voronezh' then 1 else 0 end) voronezh,
                    sum(case when region='perm' then 1 else 0 end) perm,
                    sum(case when region='saratov' then 1 else 0 end) saratov,
                    sum(case when region='krasnodar' then 1 else 0 end) krasnodar,
                    sum(case when region='warsaw' then 1 else 0 end) warsaw,
                    sum(case when region='omsk' then 1 else 0 end) omsk,
                    sum(case when region='odessa' then 1 else 0 end) odessa,
                    sum(case when region='dnepr' then 1 else 0 end) dnepropetrovsk,
                    sum(case when region='donetsk' then 1 else 0 end) donetsk,
                    sum(case when region='belarus' then 1 else 0 end) minsk,
                    sum(case when region='astana' then 1 else 0 end) astana,
                    sum(case when livesite=true then 1 else 0 end) livesite,
                    sum(case when adminpanel=true then 1 else 0 end) adminpanel,
                    sum(case when shara=true then 1 else 0 end) shara,
                    sum(case when call_type='sale' then 1 else 0 end) total
                FROM web_calls
                WHERE call_type = 'sale'
                GROUP BY
                  responsible_id,
                  extract(YEAR FROM call_date), extract(MONTH FROM call_date), extract(DAY FROM call_date)
                ORDER BY extract(YEAR FROM call_date), extract(MONTH FROM call_date), extract(DAY FROM call_date)
            )""")

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        date_start = [item for item in domain if item[0] == 'date_start']
        date_end = [item for item in domain if item[0] == 'date_end']

        new_domain = []

        if date_start:
            date_s = ('call_date', '>=', date_start[0][2])
            new_domain.append(date_s)

        if date_end:
            date_e = ('call_date', '<=', "{date} 23:59:59".format(date=date_end[0][2],))
            new_domain.append(date_e)

        return super(ResponsibleCalls, self).read_group(cr, uid, new_domain, fields, groupby, offset, limit, context, orderby)


ResponsibleCalls()
