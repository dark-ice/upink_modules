# -*- coding: utf-8 -*-
import re
import logging
from osv import osv, fields
import MySQLdb
import netsvc
from datetime import datetime
import pytz


_logger = logging.getLogger(__name__)

AVAILABLE_STATES = [
    ('draft', 'Неактивный'),
    ('active', 'Активный'),
]


class crm_lead(osv.osv):
    _name = 'crm.lead'
    _inherit = 'crm.lead'
    _columns = {
        'calles': fields.one2many('crm.phonecall', 'opportunity_id', string=u'Звонки'),
        'asterisk_date_sh': fields.datetime('Asterisk date update record'),
    }
    _defaults = {
        'asterisk_date_sh': lambda *a: datetime.now(pytz.utc),
    }


crm_lead()


class crm_phonecall(osv.osv):
    _name = 'crm.phonecall'
    _inherit = 'crm.phonecall'
    _columns = {
        'id_ast_coll': fields.char(u'ID звонка в Asterisk', size=255),
        'time_of_coll': fields.time(u'Время звонка', help=u"Время звонка в мин."),
        'duration': fields.time(u'Время разговора', help=u"Время разговора в мин."),
        'id_sphone': fields.char(u'Внутренний номер', size=16),
    }


crm_phonecall()


class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'
    _columns = {
        'callerid': fields.integer(u'Внутр. номер тел.'),
    }


res_users()


class asterisk_server(osv.osv):
    _name = 'asterisk.server'
    _columns = {
        'ast_server': fields.char(u'Сервер', size=64, help=u"Сервер MySQL Asterisk"),
        'ast_s_db': fields.char(u'База', size=64, help=u"База данных Asterisk звонков"),
        'ast_user_bd': fields.char(u'Пользователь', size=64, help=u"Пользователь MySQL"),
        'ast_pass_bd': fields.char(u'Пароль', size=64, help=u"Пароль"),
        'table': fields.char(u'Таблица звонков', size=64, help=u"Таблица звонков в базе"),
        'user_ip_host': fields.char(u'Хост', size=16, help=u"Хост"),
        'limit_rows': fields.integer(u'Лимит записей', help=u"Внимание!!! Влияет на скорость работы!"),
        'on_off': fields.boolean(u'Вкл./Выкл.', help=u"Включить или отключить работу модуля"),
        'port': fields.integer(u'Порт'),
        'n_groups': fields.integer(
            u'Игнорируемые внут. номера',
            help=u"Внутренние номера астериска, которые начинаются 9** будут игнорироваться (номера групп и тд.)"),
        'state': fields.selection(AVAILABLE_STATES, u"Статус"),
    }

    def _constraint_unique(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            unique_id = self.search(cr, uid, [])
            if unique_id != ids:
                return False
        return True

    def _constraint_limit_valid(self, cr, uid, ids):
        field = self.browse(cr, uid, ids[0])
        if field.limit_rows <= 0:
            return False
        return True

    _constraints = [
        (_constraint_unique,
         'Error: Доступен только один сервер.',
         []),
        (_constraint_limit_valid,
         'Error: Лимит записей не может быть меньше или равен 0.',
         ['limit_rows', ])
    ]

    _defaults = {
        'ast_server': lambda *a: 'localhost',
        'ast_user_bd': lambda *a: 'root',
        'ast_s_db': lambda *a: 'asteriskcdrdb',
        'user_ip_host': lambda *a: '%',
        'table': lambda *a: 'cdr',
        'limit_rows': lambda *a: 20,
        'port': lambda *a: 3306,
        'on_off': lambda *a: True,
        'state': lambda *a: 'draft',
        'n_groups': lambda *a: 9
    }

    def _get_connect(self, cr, uid, context=None):
        serv_f = self.read(cr, uid, self.search(cr, uid, [('on_off', '=', True), ], limit=1), [])
        if serv_f:
            try:
                dbmysql = MySQLdb.connect(
                    host=serv_f[0]['ast_server'],
                    user=serv_f[0]['ast_user_bd'],
                    port=serv_f[0]['port'],
                    passwd=serv_f[0]['ast_pass_bd'],
                    db=serv_f[0]['ast_s_db']
                )
                return dbmysql
            except Exception, e:
                _logger.info("Error connection to db: %s" % str(e))

        return False

    def check_connect(self, cr, uid, dbmysql, ids, context=None):
        try:
            dbmysql = self._get_connect(cr, uid)
            dbmysql.close()
            raise osv.except_osv("Test is successfully completed", '')
        except osv.except_osv, success_message:
            raise success_message
        except Exception, error:
            raise osv.except_osv("Test fail", "Error: %s" % str(error))

    def get_colls(self, cr, uid, context=None):
        _logger.info("Check call")
        dbmysql = self._get_connect(cr, uid)
        if dbmysql:

            read_rows = 0
            write_rows = 0

            try:
                db = dbmysql.cursor()
            except Exception, e:
                _logger.info("Cant connect to MySql")
                return True

            serv_f = self.read(cr, uid, self.search(cr, uid, [('on_off', '=', True), ('state', '=', 'active'), ], limit=1), [])
            if serv_f:
                obj_ir_model_data = self.pool.get('ir.model.data')
                tel_reference_pool = self.pool.get('tel.reference')

                pe = re.compile('\d+', re.UNICODE)

                # Start selected colls
                sql = """SELECT * FROM %s LIMIT %s;""" % (serv_f[0]['table'] + '_report', serv_f[0]['limit_rows'])
                db.execute(sql)
                res = db.fetchall()

                if res:
                    sql_del_rows = []

                    for item in res:
                        read_rows += 1
                        sql_del_rows.append(str(item[0]))
                        ids_rw = []
                        type_coll = []
                        user = False
                        id_sphone = ''
                        in_num = 0
                        categ = ''

                        if item[8] == 'inbound':
                            in_num = "".join(pe.findall(item[4]))
                            id_sphone = item[4]
                            phone = str(item[3])
                            categ = 'categ_phone1'
                        elif item[8] == 'outbound':
                            in_num = "".join(pe.findall(item[3]))
                            phone = str(item[4])
                            id_sphone = item[3]
                            categ = 'categ_phone2'

                        ids_rw = tel_reference_pool.search(cr, uid, [('phone_for_search', '=', phone)])
                        id_user = self.pool.get('res.users').search(cr, uid, [('callerid', '=', in_num)], limit=1)
                        type_coll = obj_ir_model_data.read(
                            cr,
                            uid,
                            obj_ir_model_data.search(
                                cr,
                                uid,
                                [
                                    ('name', '=', categ),
                                    ('model', '=', 'crm.case.categ')
                                ]
                            ),
                            ['res_id']
                        )

                        if ids_rw:
                            if id_user:
                                user = id_user[0]
                                tel_date = tel_reference_pool.browse(cr, uid, ids_rw)
                                for val in tel_date:
                                    write_rows += 1
                                    self.pool.get('crm.phonecall').create(
                                        cr,
                                        1,
                                        {
                                            'id_ast_coll': item[2],
                                            'date': item[1],
                                            'partner_phone': val.phone_for_search,
                                            'id_sphone': id_sphone,
                                            'time_of_coll': item[5],
                                            'duration': item[6],
                                            'name': item[7],
                                            'user_id': user,
                                            'categ_id': type_coll[0]['res_id'],
                                            'state': 'open',
                                            'opportunity_id': val.crm_lead_id.id,
                                            'partner_id': val.res_partner_id.id,
                                            'partner_address_id': val.partner_address_id.id,
                                        })
                    try:
                        format_strings = ','.join(['%s'] * len(sql_del_rows))
                        sql = "DELETE FROM %s WHERE id IN (%s);" % (serv_f[0]['table'] + '_report', format_strings)
                        db.execute(sql, sql_del_rows)
                        #_logger.info(sql)
                        _logger.info(u"Report: Удалено %s строк" % str(len(sql_del_rows)))
                        _logger.info(u"Report: Получено записей %s, записано в историю звонков %s" % (str(read_rows), str(write_rows)))
                    except Exception, e:
                        _logger.info("Error sql: %s" % str(e))
                dbmysql.close()
                return True

        return False

    def set_script_sql(self, cr, uid, ids, context=None):
        servsql = self.browse(cr, uid, ids[0], context)
        dbmysql = self._get_connect(cr, uid)
        if dbmysql:
            db = dbmysql.cursor()
            sql_table = """
                CREATE TABLE IF NOT EXISTS `%s` (
                `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `calldate` datetime NOT NULL,
                `colle_id` varchar(32) NOT NULL,
                `number` varchar(80),
                `dnumber` varchar(80),
                `tcoll` TIME,
                `tmcoll` TIME,
                `status` varchar(45),
                `type` varchar(10) );
                """ % (servsql.table + '_report')

            sql_triger = """
                CREATE DEFINER=`%s`@`%s` TRIGGER `%s` AFTER INSERT ON `%s` FOR EACH ROW BEGIN
                    IF length(NEW.src) = 3 AND length(NEW.dst) >= 10 AND substr(NEW.src,1,1)!='%s' THEN
                           INSERT INTO %s SET
                           calldate = NEW.calldate,
                           colle_id = NEW.uniqueid,
                           number = NEW.src,
                           dnumber = RIGHT(NEW.dst,10),
                           tcoll = sec_to_time(NEW.duration),
                           tmcoll = sec_to_time(NEW.billsec),
                           status = NEW.disposition,
                           type = 'outbound';
                    ELSEIF length(NEW.dst) = 3 AND length(NEW.src) >= 10 AND substr(NEW.dst,1,1)!='%s' THEN
                           INSERT INTO %s SET
                           calldate = NEW.calldate,
                           colle_id = NEW.uniqueid,
                           number = RIGHT(NEW.src,10),
                           dnumber = NEW.dst,
                           tcoll = NEW.duration,
                           tmcoll = NEW.billsec,
                           status = NEW.disposition,
                           type = 'inbound';
                    END IF;
                END;
                """ % (servsql.ast_user_bd, servsql.user_ip_host, 'insert_' + servsql.table, servsql.table,
                       servsql.n_groups, servsql.table + '_report', servsql.n_groups, servsql.table + '_report')
            try:
                db.execute(sql_table)
                db.execute(sql_triger)
            except Exception, e:
                _logger.info("Error set view: %s" % str(e))
                dbmysql.close()
                raise osv.except_osv("Error set view", "Reason: %s" % e)

            dbmysql.close()
            self.write(cr, uid, ids, {'state': 'active'}, context=None)
        else:
            raise osv.except_osv("Error connect to db", "Reason: Error connection to db")
        return True

    def cancel(self, cr, uid, ids, context=None):
        servsql = self.browse(cr, uid, ids[0], context=None)
        dbmysql = self._get_connect(cr, uid)
        if dbmysql:
            db = dbmysql.cursor()
            sql_table = """DROP TABLE IF EXISTS `%s`;""" % (servsql.table + '_report')

            sql_triger = """DROP TRIGGER IF EXISTS `%s`;""" % ('insert_' + servsql.table)
            try:
                db.execute(sql_table)
                db.execute(sql_triger)
            except Exception, e:
                _logger.info("Error set view: %s" % str(e))
                dbmysql.close()
                raise osv.except_osv("Error set view", "Reason: %s" % e)

            dbmysql.close()
            self.write(cr, uid, ids, {'state': 'draft'}, context=None)
            return True
        else:
            raise osv.except_osv("Error connect to db", "Reason: Error connection to db")

    def unlink(self, cr, uid, ids, context=None):
        _logger.info("Error cant unlink")
        raise osv.except_osv("Error cant unlink", "Error cant unlink")


asterisk_server()
