# -*- coding: utf-8 -*-

from osv import osv, fields
import re
import time
import netsvc
from tools import cache
import socket
import logging


def _gen_cache_clear(method):
    def func(self, cr, *args, **kwargs):
        s = super(asterisk_calls_config, self)
        r = getattr(s, method)(cr, *args, **kwargs)
        self.is_enable.clear_cache(self)
        return r
    return func


class activ_asterisk_calls(osv.osv):
    _name = 'activ.asterisk.calls'
    _columns = {
        'name': fields.char('Номер входящего звонка', size=65),
        'create_date': fields.datetime('Дата звонка', readonly=True, select=True),
        'sid': fields.integer('Номер менеджера'),
        'city': fields.char('Город', size=65),
        'lead_id': fields.many2one('crm.lead', 'Кандидат'),
        'partner_id': fields.many2one('res.partner', 'Партнер'),
        'active': fields.boolean('флаг нового окна', size=65),
    }
    _defaults = {
        'active': lambda *a: True,
    }
    _order = "id desc"
    __logger = logging.getLogger(_name)

    def get_lead_partner_by_phone(self, cr, uid):
        var = {}
        result = []
        p = re.compile('\d+', re.UNICODE)
        tel_obj = self.pool.get('tel.reference')
        ser_conf = self.pool.get('asterisk.server').read(cr, uid, self.pool.get('asterisk.server').search(cr, uid, [('on_off', '=', True)], limit=1), [])[0]
        user_calln = self.pool.get('res.users').read(cr, uid, uid, ['callerid', 'login'])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ser_conf['ast_server'], ser_conf['ami_port']))
            params = [
                "Action: login",
                "Events: off",
                "Username: %s" % (ser_conf['ami_login']),
                "Secret: %s" % (ser_conf['ami_pass']),
                "",
            ]
            s.send("\r\n".join(params) + "\r\n")
            time.sleep(0.2)

            self.__logger.debug("AMI(%s)",  user_calln['login'])

            s.send("Action: Status\r\n\r\n")
            time.sleep(1)
            massage = s.recv(38000)
            for v in massage.split('\r\n\r\n'):
                t_dict = {}
                for x in v.split('\r\n'):
                    y = x.split(': ')
                    if len(y) == 2:
                        t_dict.update(dict([y]))
                result.append(t_dict)

            s.send("Action: Logoff\r\n\r\n")
            time.sleep(0.2)
            self.__logger.debug("AMI(%s)",  user_calln['login'])
            s.close()
        except socket.error, e:
            self.__logger.debug("AMI connect failed.\nError: %s", e)

        #result.append({'CallerIDNum': '140', 'ConnectedLineName': '(Kiev)74955448352', 'ConnectedLineNum': '74955448352'})
        print result
        for val in result:
            if val.get('Items'):
                self.__logger.debug("Items get: %s", val.get('Items'))

            if val.get('CallerIDNum') == str(user_calln['callerid']) and len(val.get('ConnectedLineNum')) > 7:
                num_tel = "".join(p.findall(val.get('ConnectedLineNum')))[-10:]
                num_city = ''

                self.__logger.debug("Call from: %s", val.get('ConnectedLineName'))

                if val.get('ConnectedLineName'):
                    num_city = val.get('ConnectedLineName').split(')')[0][1:]  # (Kiev)74955448352
                res_id = tel_obj.search(cr, uid, [('phone_for_search', 'like', num_tel)], context=None)

                if res_id:
                    res = tel_obj.browse(cr, uid, res_id[0], context=None)
                    partner_id = 0
                    if res.partner_address_id.id and not res.res_partner_id.id:
                        id_partner_addr = self.pool.get('res.partner.address').search(cr, uid, [('id', '=', res.partner_address_id.id)])[0]
                        partner_id = self.pool.get('res.partner.address').browse(cr, uid, id_partner_addr).partner_id or False
                        if partner_id:
                            partner_id = partner_id.id
                    else:
                        partner_id = res.res_partner_id.id

                    if partner_id:
                        var.update(
                            {
                                'type': 'res.partner',
                                'id': partner_id,
                                'name': res.res_partner_id.name,
                                'city': num_city,
                                'phone': num_tel
                            }
                        )
                    else:
                        var.update(
                            {
                                'type': 'crm.lead',
                                'id': res.crm_lead_id.id,
                                'name': res.crm_lead_id.name,
                                'city': num_city,
                                'phone': num_tel
                            }
                        )
                else:
                    creat_val = {}
                    crm_obj = self.pool.get('crm.lead')
                    values = self.pool.get('asterisk.calls.config').check_user(cr, uid)
                    if values['act_client_type'] == 'contact':
                        creat_val.update({'name': u'Розничный клиент'})
                    else:
                        creat_val.update({'name': num_tel})

                    creat_val.update(
                        {
                            'city': num_city,
                            'section_id': crm_obj.default_get(cr, uid, ['section_id'])['section_id'],
                            'responsible_user': crm_obj.default_get(cr, uid, ['responsible_user'])['responsible_user'],
                            'user_id': crm_obj.default_get(cr, uid, ['user_id'])['user_id'],
                            'partner_type': crm_obj.default_get(cr, uid, ['partner_type'])['partner_type'],
                            'company_type': values['act_client_type'],
                        }
                    )
                    lead_id = crm_obj.create(cr, uid, creat_val, context=None)
                    tel_obj.create(cr, uid, {'phone': num_tel, 'crm_lead_id': lead_id}, context=None)
                    var.update(
                        {
                            'type': 'crm.lead',
                            'id': lead_id,
                            'name': 'Новый кандидат',
                            'city': num_city,
                            'phone': num_tel
                        }
                    )
        if not var:
            self.__logger.debug("No active calls")

        return var

activ_asterisk_calls()


class asterisk_calls_config(osv.osv):
    _name = 'asterisk.calls.config'
    _columns = {
        'group_id': fields.many2one('res.groups', 'Группа доступа', required=True),
        'act_window_lead_id': fields.many2one(
            'ir.actions.act_window',
            'Окно формы кандидата',
            required=True,
            domain=[('res_model', '=', 'crm.lead')]
        ),
        'act_window_partner_id': fields.many2one(
            'ir.actions.act_window',
            'Окно формы партнера',
            required=True,
            domain=[('res_model', '=', 'res.partner')]
        ),
        'type_lead_pertner': fields.selection(
            [
                ('contact', 'Контакт центр'),
                ('inksystem', 'СНГ Inksystem'),
                ('upsale', 'UpSale'),
                ('eu', 'СНГ ЕС')
            ], 'Тип контакта'),
    }

    create = _gen_cache_clear('create')
    write = _gen_cache_clear('write')
    unlink = _gen_cache_clear('unlink')

    def check_user(self, cr, uid):
        val = {}
        fields_user = self.pool.get('res.users').browse(cr, uid, uid)
        fields_self = self.browse(cr, uid, self.search(cr, uid, []))
        ug = [uf.id for uf in fields_user.groups_id]
        rows = [fu for fu in fields_self if fu.group_id.id in ug]
        if rows:
            val['act_lead'] = rows[0].act_window_lead_id.id
            val['act_part'] = rows[0].act_window_partner_id.id
            val['act_client_type'] = rows[0].type_lead_pertner
        return val

    @cache(skiparg=3, timeout=300)
    def is_call_enable(self, cr, uid):
        domain = [('id', '=', uid), ('callerid', '!=', 0)]
        return self.search_count(cr, uid, domain) != 0

    @cache(skiparg=3)
    def get_default_text(self, cr, uid):
        #if self.check_user(cr, uid):
        #    return '<a href="#"><img src="/asterisk_incoming_calls/static/images/ast_call_butt_beta.png"/>Открыть звонок</a>'
        #else:
        return ''

asterisk_calls_config()


class asterisk_server(osv.osv):
    _name = 'asterisk.server'
    _inherit = 'asterisk.server'
    _columns = {
        'ami_login': fields.char('Логин AMI', size=64),
        'ami_pass': fields.char('Пароль AMI', size=64),
        'ami_port': fields.integer('Порт AMI'),
    }
    _defaults = {
        'ami_port': lambda *a: 5038,
    }

asterisk_server()
