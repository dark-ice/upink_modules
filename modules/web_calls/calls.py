# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
import re
import socket
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model
import time
import pytz

try:
    import json
except ImportError:
    import simplejson as json

import web.common.http as openerpweb
from tools.translate import _
from Asterisk import Manager


_logger = logging.getLogger(__name__)
tzlocal = pytz.timezone(tools.detect_server_timezone())

REGIONS = {
    'msk': set(['yandexmarket_MSK', 'SEO_MSK', 'kont_google_MSK', 'kont_yandex_MSK', 'smm_MSK', 'catalog_MSK', 'seo_MSK',
            'yandexmarket_2_MSK', 'Moskva', 'MSK', 'jivosite.com', 'HotRussia']),
    'spb': set(['yandexmarket_SPB', 'SEO_SPB', 'kont_google_SPB', 'kont_yandex_SPB', 'smm_SPB', 'catalog_SPB', 'seo_SPB',
            'St_Piter', 'SPb-78124948862',  'service-Russia', 'kont_yandex_SPB']),
    'kiev': set(['yandexmarket_KIEV', 'SEO_KIEV', 'kont_google_Kiev', 'kont_yandex_KIEV', 'smm_KIEV', 'catalog_KIEV',
             'seo_KIEV', 'Kiev', 'Kiev_region', 'Kiev-service', 'SEO_KIEV']),
    'ekb': set(['Ekatirenburg', 'EKT-reg']),
    'novosibirsk': set(['Novosibirsk', 'Novosibirsk-new']),
    'chelyabinsk': set(['Chelyabinsk', 'Chel_region']),
    'samara': set(['Samara', 'Samara-78462265810']),
    'nino': set(['NizhniyNovgorod', 'NizhniyNovgorod-region']),
    'kazan': set(['Kazan', 'Kazan-region']),
    'rostov': set(['Rostov', 'Rostov-site']),
    'irkutsk': set(['Irkutsk', 'Irkutsk1']),
    'alm': set(['Alm_region', 'Kazahstan',]),
    'krasnodar': set(['Krasnodar', 'Krasnodar1']),
    'volgograd': set(['Volgograd', 'Volgograd-region']),
    'ufa': set(['Ufa', ]),
    'krasnoyarsk': set(['Krasnoyarsk', ]),
    'perm': set(['Perm', 'Perm-region']),
    'omsk': set(['Omsk', ]),
    'odessa': set(['Odessa', ]),
    'dnepr': set(['Dnepr', ]),
    'donetsk': set(['Donetck', ]),
    'voronezh': set(['Voronej', 'Voronej-region']),
    'saratov': set(['Saratov', 'Saratov1']),
    'kharkov': set(['Kharkov', ]),
    'belarus': set(['Belarus', 'Belarus-Velcom', 'opt-belarus', 'Minsk_Velcome']),
    'warsaw': set(['HotVarshava', 'Varshava', 'Lndn1', 'Lndn2', 'Lndn3', 'Lndn4', 'Wrszw1', 'Wrszw2', 'Wrszw3']),
    'astana': set(['astana', ]),
}

CITIES = (
    ('msk', u'Москва'),
    ('spb', u'Санкт-Петербург'),
    ('kiev', u'Киев'),
    ('ekb', u'Екатеринбург'),
    ('novosibirsk', u'Новосибирск'),
    ('chelyabinsk', u'Челябинск'),
    ('samara', u'Самара'),
    ('nino', u'Нижний Новгород'),
    ('kazan', u'Казань'),
    ('rostov', u'Ростов на Дону'),
    ('irkutsk', u'Иркутск'),
    ('alm', u'Алматы'),
    ('krasnodar', u'Краснодар'),
    ('volgograd', u'Волгоград'),
    ('ufa', u'Уфа'),
    ('krasnoyarsk', u'Красноярск'),
    ('perm', u'Пермь'),
    ('omsk', u'Омск'),
    ('odessa', u'Одесса'),
    ('dnepr', u'Днепропетровск'),
    ('donetsk', u'Донецк'),
    ('voronezh', u'Воронеж'),
    ('kharkov', u'Харьков'),
    ('saratov', u'Саратов'),
    ('belarus', u'Минск'),
    ('warsaw', u'Варшава'),
    ('astana', u'Астана'),
    ('unknown', u'Неизвестный город')
)


def format_date_tz(date, tz=None):
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
    if tz is None:
        tz = pytz.timezone(tools.detect_server_timezone())
    return tz.normalize(date).strftime('%Y-%m-%d %H:%M:%S')


class WebCalls(Model):
    _name = 'web.calls'
    _order = 'id DESC'

    _columns = {
        'name': fields.char('Номер входящего звонка', size=10),
        'create_date': fields.datetime(string='Дата звонка', readonly=True, select=True),
        'sid': fields.integer('Номер менеджера'),
        'city': fields.char('Город', size=65),
        'region': fields.selection(CITIES, 'Город', required=True),
        'responsible_id': fields.many2one('res.users', 'Менеджер'),
        'date': fields.date('Дата'),
        'time': fields.float('Время'),
        'call_date': fields.datetime('Дата звонка'),
        'call_type': fields.selection(
            (
                ('sale', 'Продажа'),
                ('consultation', 'Консультация'),
                ('no_product', 'Запрос на отсутствующий товар'),
                ('qa', 'Тех.поддержка'),
                ('order', 'Уточнения по оформленному заказу'),
                ('atc', 'Проблема с АТС'),
                ('number', 'Ошиблись номером'),
            ), 'Тип звонка'
        ),
        'account': fields.char('Счет', size=250),
        'po': fields.char('ПО', size=250),
        'invoice': fields.char('Товарный чек', size=250),

        'livesite': fields.boolean('Продажи с Живосайта'),
        'adminpanel': fields.boolean('Продажи с Админпанели'),
        'shara': fields.boolean('Халява'),
        'sale_type': fields.selection(
            (
                ('-', '-'),
                ('py', 'ПУ'),
                ('snpch', 'СНПЧ или ПЗК'),
                ('ink', 'Чернила'),
                ('another', 'Прочее'),

            ), 'Тип продажи'
        ),

        'consultation': fields.char('Вопрос консультации', size=250),
        'no_product': fields.char('Запрос на отсутствующий товар', size=250),

        'date_start': fields.date('c', select=True),
        'date_end': fields.date('по', select=True),
    }

    _defaults = {
        'responsible_id': lambda s, c, u, cnt: u,
        'call_date': lambda *a: datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'sale_type': '-',
    }

    def get_default_text(self, cr, uid):
        if self.pool.get('res.users').search(cr, uid, [('id', '=', uid), ('groups_id', 'in', [169, 170])]):
            return '<a href="#"><img src="/web_calls/static/src/img/uv_favicon.png" />Звонок</a>'
        else:
            return ''

    def _get_connection_result(self, cr, user, user_calln):
        server_pool = self.pool.get('asterisk.server')
        result = []

        server_ids = server_pool.search(cr, user, [('on_off', '=', True)], limit=1)
        if server_ids:
            ser_conf = self.pool.get('asterisk.server').read(cr, user, server_ids[0], [])
        else:
            raise osv.except_osv('SERVER', 'Добавьте рабочий сервер')

        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            my_socket.connect((ser_conf['ast_server'], ser_conf['ami_port']))
            params = [
                "Action: login",
                "Events: off",
                "Username: %s" % (ser_conf['ami_login']),
                "Secret: %s" % (ser_conf['ami_pass']),
                "",
            ]
            my_socket.send("\r\n".join(params) + "\r\n")
            time.sleep(0.2)

            _logger.debug("AMI(%s)", user_calln['login'])

            my_socket.send("Action: Status\r\n\r\n")
            time.sleep(1)
            message = my_socket.recv(38000)
            print message
            for v in message.split('\r\n\r\n'):
                t_dict = {}
                for x in v.split('\r\n'):
                    y = x.split(': ')
                    if len(y) == 2:
                        t_dict.update(dict([y]))
                result.append(t_dict)

            print result

            my_socket.send("Action: Logoff\r\n\r\n")
            time.sleep(0.2)
            _logger.debug("AMI(%s)", user_calln['login'])
            my_socket.close()
        except socket.error, e:
            _logger.debug("AMI connect failed.\nError: %s", e)
            #  comment to push

        return result

    def _get_asterisk_server_from_user(self, cr, uid, user, context=None):
        """Returns an asterisk.server browse object"""
        server_pool = self.pool.get('asterisk.server')
        server_ids = server_pool.search(cr, uid, [('on_off', '=', True)], limit=1)

        if not server_ids:
            raise osv.except_osv(_('Error :'),
                                 _("No Asterisk server configured for the company '%s'.") % user.company_id.name)
        else:
            #ast_server = self.browse(cr, uid, asterisk_server_ids[0], context=context)
            ast_server = server_pool.read(cr, uid, server_ids[0], [])
        return ast_server

    def _connect_to_asterisk(self, cr, uid, context=None):
        """
        Open the connection to the asterisk manager
        Returns an instance of the Asterisk Manager

        """
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        ast_server = self._get_asterisk_server_from_user(cr, uid, user, context=context)

        _logger.debug("User's phone : %s/%s" % (user.callerid, user.name))
        _logger.debug("Asterisk server = %s:%d" % (ast_server['ast_server'], ast_server['ami_port']))

        # Connect to the Asterisk Manager Interface
        try:
            ast_manager = Manager.Manager(
                (
                    ast_server['ast_server'],
                    ast_server['ami_port']
                ),
                ast_server['ami_login'],
                ast_server['ami_pass']
            )
            _logger.debug("Manager []: %s", ast_manager)
        except Exception, e:
            _logger.error("Error in the Originate request to Asterisk server %s" % ast_server['ast_server'])
            _logger.error("Here is the detail of the error : '%s'" % e)
            raise osv.except_osv(_('Error :'), _(
                "Problem in the request from OpenERP to Asterisk. Here is the detail of the error: '%s'" % e))

        return user, ast_server, ast_manager

    def open_call(self, cr, uid, context=None):
        user, ast_server, ast_manager = self._connect_to_asterisk(cr, uid, context=context)
        calling_party_number = False
        city = ''
        phone = ''
        try:
            list_chan = ast_manager.Status()
            for chan in list_chan.values():
                if chan.get('CallerIDNum') == str(user.callerid):
                    _logger.info("UserCallerId: %s" % str(user.callerid))
                    _logger.info("CallerIDNum: %s" % str(chan.get('CallerIDNum')))
                    _logger.info("ConnectedLineName: %s" % str(chan.get('ConnectedLineName')))
                    calling_party_number = chan.get('ConnectedLineNum')
                    if chan.get('ConnectedLineName'):
                        indx = chan['ConnectedLineName'].find(')')
                        if indx:
                            city = chan['ConnectedLineName'][1:indx]
                    break
        except Exception, e:
            _logger.error("Error in the Status request to Asterisk server %s" % ast_server['ast_server'])
            _logger.error("Here is the detail of the error : '%s'" % e)
            raise osv.except_osv(_('Error :'),
                                 _("Can't get calling number from  Asterisk.\nHere is the error: '%s'" % e))

        finally:
            ast_manager.Logoff()

        _logger.debug("The calling party number is '%s'" % calling_party_number)

        now = datetime.strptime(format_date_tz(datetime.now(pytz.utc)), "%Y-%m-%d %H:%M:%S")
        if calling_party_number:
            phone = calling_party_number[-10:]
        return {
            'region': get_city(get_region(city))[1],
            'city': city,
            'phone': phone,
            'date': now.strftime("%d/%m/%Y"),
            'time': now.strftime("%H.%M"),
            'call_datetime': now.strftime("%d/%m/%Y %H:%M:%S"),
            'responsible_id': user.id,
            'responsible': user.name
        }

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        for indx, item in enumerate(domain):
            if item[0] == 'date_start':
                domain[indx] = ('call_date', '>=', item[2])
            if item[0] == 'date_end':
                domain[indx] = ('call_date', '<=', "{date} 23:59:59".format(date=item[2],))

        return super(WebCalls, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)
WebCalls()


def get_region(prefix):
    city = 'unknown'
    for key, region in REGIONS.items():
        if prefix in region:
            return key
    return city


def get_city(state):
    city = [item for item in CITIES if state in item]
    if city:
        return city[0]
    return 'unknown', u'Неизвестный город'


class calls_create(openerpweb.Controller):
    _cp_path = '/web/calls'

    def fields_get(self, req, model):
        Model = req.session.model(model)
        fields = Model.fields_get(False, req.session.eval_context(req.context))
        return fields

    @openerpweb.jsonrequest
    def create(self, req, city, region, phone, call_time, call_date, call_type, responsible_id, account, po, invoice,
               consultation, no_product, sale_type):
        call_datetime = datetime.strptime("{date} {time}:00".format(date=call_date, time=call_time.replace('.', ':')),
                                          "%d/%m/%Y %H:%M:%S") - timedelta(hours=3)

        create_id = req.session.model('web.calls').create(
            {
                #'city': get_city(city)[0],
                'city': city,
                'region': get_city(region)[0],
                'name': phone,
                #'time': call_time,
                #'date': call_date,
                'call_type': call_type,
                'call_date': call_datetime,
                'responsible_id': responsible_id,
                'account': account,
                'po': po,
                'invoice': invoice,
                'consultation': consultation,
                'no_product': no_product,
                'sale_type': sale_type
            }
        )
        state = True if create_id else False
        return [{'state': state}]