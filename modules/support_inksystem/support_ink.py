# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


class supp_services_stage(Model):
    _name = "supp.services.stage"
    _description = u"Справочник сервисных услуг"
    _order = 'name'

    _columns = {
        'name': fields.char('Услуга', size=255, required=True, select=True),
        'cost': fields.integer('Стоимость'),
        'comment': fields.text('Примечание'),
    }

supp_services_stage()


class supp_sale(Model):
    _name = "supp.sale"
    _description = u"Квитанции тех. обслуживания"
    _order = 'create_date desc'

    def get_days(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['create_date', 'ready_date', 'putup_date']):
            val = timedelta(days=0)
            if name == 'day_on_repairs':

                start_date = datetime.strptime(record['create_date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
                end_date = datetime.now(pytz.utc)
                if record['ready_date']:
                    end_date = datetime.strptime(record['ready_date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)

                val = end_date - start_date
            else:
                if record['ready_date']:
                    end_date = datetime.strptime(record['ready_date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
                    start_date = datetime.now(pytz.utc)
                    if record['putup_date']:
                        start_date = datetime.strptime(record['putup_date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
                    val = start_date - end_date

            res[record['id']] = val.days
        return res

    def search_days(self, cr, uid, obj, name, args, context):
        ids = set()
        for cond in args:
            amount = cond[2]
            if name == 'day_on_repairs':
                cr.execute("select id, supp_sale WHERE EXTRACT(DAY FROM COALESCE(ready_date, now() at time zone 'UTC') - create_date) = %s;",(amount,))
            else:
                cr.execute("select id, supp_sale WHERE EXTRACT(DAY FROM COALESCE(putup_date, now() at time zone 'UTC') - ready_date) = %s;",(amount,))

            res_ids = set(id[0] for id in cr.fetchall())

            ids = ids and (ids & res_ids) or res_ids

        """
        SELECT
  city,
  concat(c_create, '(', case when c_create=0 then 0 else cw_create * 100/c_create end, '%)') create_all,
  concat(c_ready, '(',case when c_ready=0 then 0 else cw_ready * 100/c_ready end, '%)') ready_all,
  concat(c_putup, '(',case when c_putup=0 then 0 else cw_putup * 100/c_putup end, '%)') putup_all,
  d1,
  d2,
  d3
FROM (
  SELECT
    c.name city,
    sum(case when s.create_date < now() then 1 else 0 end) c_create,
    sum(case when s.create_date < now() and type_supp='warranty' then 1 else 0 end) cw_create,

    sum(case when s.ready_date < now() then 1 else 0 end) c_ready,
    sum(case when s.ready_date < now() and type_supp='warranty' then 1 else 0 end) cw_ready,

    sum(case when s.putup_date < now() then 1 else 0 end) c_putup,
    sum(case when s.putup_date < now() and type_supp='warranty' then 1 else 0 end) cw_putup,

    sum(case when EXTRACT(DAY FROM COALESCE(s.ready_date, now() at time zone 'UTC') - s.create_date) > 14 AND s.create_date < now() then 1 else 0 end) d1,
    sum(case when EXTRACT(DAY FROM COALESCE(s.ready_date, now() at time zone 'UTC') - s.create_date) > 14 then 1 else 0 end) d2,

    sum(case when state = 'repiar_end' then 1 else 0 end) d3,

  FROM
    supp_sale s
    LEFT JOIN supp_city_stage c on (c.id=s.city_id)
  GROUP BY
    c.name
  ORDER BY c.name
) a;
"""
        if ids:
            return [('id', 'in', tuple(ids))]
        return [('id', '=', '0')]

    _columns = {
        # Head
        'user_id': fields.many2one(
            'res.users',
            'Автор',
            readonly=True,
            help='Сотрудник создавший квитанцию'),
        'city_id': fields.many2one(
            'supp.city.stage',
            'Город',
            select=True,
            readonly=True,
            states={
                'draft': [('readonly', False), ('required', True)],
                'repiar': [('readonly', False), ('required', True)]
            },
            help='Город'),
        'create_date': fields.datetime(
            'Дата создания',
            select=True,
            readonly=True,
            help='Дата создания квитанции. При создании проставляется текущая дата'),
        'getup_date': fields.datetime(
            'Дата приемки в ремонт',
            select=True,
            required=True,
            states={
                'closed': [('readonly', True)]
            },
            help='Дата приемки в ремонт. Проставляется текущая дата при переводе квитанции в ремонт.\n'
                 'При необходимости дату можно сменить'),
        'ready_date': fields.datetime(
            'Дата окончания ремонта',
            select=True,
            help='Дата окончания ремонта. Проставляется дата перевода квитанции на этап "Ремонт окончен"'),
        'putup_date': fields.datetime(
            'Дата выдачи',
            select=True,
            help='Дата выдачи. Проставляется дата перевода квитанции на этап "Принтер выдан"'),
        'id': fields.integer(
            'Номер квитанции',
            select=True,
            readonly=True,
            help='Номер квитанции'),
        'trademark': fields.char(
            'Торговая марка',
            size=255,
            select=True,
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Торговая марка оборудования.'),
        'model': fields.char(
            'Модель',
            size=255,
            select=True,
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Модель оборудования.'),
        'telephone': fields.char(
            'Номер телефона клиента',
            size=125,
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Номер телефона клиента.'),
        'sirial_number': fields.char(
            'Серийный номер',
            size=125,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Серийный номер оборудования.'),
        'client_name': fields.char(
            'ФИО клиента',
            size=125,
            select=True,
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='ФИО клиента.'),
        'type_supp': fields.selection(
            [
                ('warranty', 'гарантийный'),
                ('no_warranty', 'не гарантийный'),
            ],
            'Вид ремонта',
            select=True,
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Вид ремонта: гарантийный, не гарантийный.'),
        'type_client': fields.selection(
            [
                ('retail', 'Розничный клиент'),
                ('dealer', 'Дилер')
            ],
            'Тип клиента',
            help='Тип клиента: дилер, розничный клиент.'),
        'defect': fields.text(
            'Заявленная неисправность',
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Текстовое поле, заполняется вручную. Обязательное к заполнению'),
        'reason': fields.text(
            'Причина возникновения неисправности',
            help='Текстовое поле, заполняется вручную. Не обязательное к заполнению'),
        'appearance': fields.text(
            'Внешний вид продукции',
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Текстовое поле, заполняется вручную. Обязательное к заполнению'),
        'completion': fields.text(
            'Комплектность',
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Текстовое поле, заполняется вручную. Обязательное к заполнению'),
        'comment': fields.text(
            'Коментарии',
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Текстовое поле, заполняется вручную. Не обязательное к заполнению'),
        'employees_id': fields.many2one(
            'hr.employee',
            'Ответственный за ремонт',
            select=True,
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'repiar': [('readonly', False)]
            },
            help='Сотрудник ответственный за ремонт.'),
        'rep_ids': fields.one2many(
            'supp.components.stage',
            'supp_sale_id',
            'Замененные детали',
            help='При нажатии на кнопку "Создать" заполняется таблица с колонками: '
                 'Наименование (замененной детали), стоимость, количество (шт.)'),
        'serv_ids': fields.many2many(
            'supp.services.stage',
            'supp_services_supp_ink_rel',
            'supp_ink_id',
            'supp_services_id',
            string='Оказанные услуги',
            help='При нажатии на кнопку "Создать" можно выбрать из списка необходимую услугу, предоставленную клиенту.'),
        'state': fields.selection(
            [
                ('draft', 'черновик'),
                ('repiar', 'принят в ремонт'),
                ('repiar_end', 'ремонт окончен'),
                ('closed', 'выдан'),
            ],
            'Состояние',
            select=True,
            help='Поле отображает текущий этап данного бланка.'),
        'note_ids': fields.one2many(
            'supp.sale.notes',
            'supp_id',
            'Обзвон',
            help='Таблица для добавления комментария после звонка клиенту.'),
        'last_comment': fields.related(
            'note_ids',
            'title',
            type='char',
            size=128,
            string='Комментарий',
            help='Последний комментарий по текущей заявке.'),

        'day_on_repairs': fields.function(
            get_days,
            fnct_search=search_days,
            method=True,
            string='Дней до окончания ремонта',
            type='integer',
        ),

        'day_over_repairs': fields.function(
            get_days,
            fnct_search=search_days,
            method=True,
            string='Дней после окончания ремонта',
            type='integer',
        ),
    }

    def add_note(self, cr, uid, ids, context=None):
        view_id = self.pool.get('ir.ui.view').search(
            cr,
            uid,
            [
                ('name', 'like', 'supp.sale.add.note.form1'),
                ('model', '=', self._name)
            ])
        return {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'supp.sale.notes',
            'name': 'Обзвон',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': {
                'supp_id': ids[0],
            },
            'target': 'new',
            'nodestroy': True,
        }

    def onchange_city(self, cr, uid, ids, city_id, context=None):
        result = {}
        if city_id:
            employ_data = self.pool.get('supp.city.stage').read(cr, uid, city_id, ['employees_ids'], context=context)
            result['employees_id'] = [('id', 'in', employ_data['employees_ids'])]
        return {'domain': result}

    _defaults = {
        'user_id': lambda s, c, u, cntx: u,
        'getup_date': fields.datetime.now,
        'state': 'draft',
    }

    def _check_start_end_data(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            date_end = False
            date_create = False
            if field.putup_date:
                date_end = datetime.strptime(field.putup_date, "%Y-%m-%d %H:%M:%S")
            if field.getup_date:
                date_create = datetime.strptime(field.getup_date, "%Y-%m-%d %H:%M:%S")
            if date_create and date_end:
                if date_create > date_end:
                    return False
        return True

    _constraints = [
        (
            _check_start_end_data,
            'Срок выдачи продукта позже чем срок принятия в ремонт',
            ['Срок выдачи продукта', 'Срок принятия в ремонт', ]
        ),
    ]

    def action_repiar(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'repiar'})

    def action_repiar_end(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'repiar_end', 'ready_date': fields.datetime.now()})

    def action_closed(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'closed', 'putup_date': fields.datetime.now()})


supp_sale()


class supp_components_stage(Model):
    _name = "supp.components.stage"
    _description = u"Справочник замененных деталей"
    _order = 'name'
    _columns = {
        'supp_sale_id': fields.many2one(
            'supp.sale',
            'Квитанции тех. обслуживания'),
        'name': fields.text(
            'Наименование',
            required=True,
            select=True),
        'cost': fields.integer('Стоимость'),
        'num': fields.integer('Количество, шт'),
    }

supp_components_stage()


class supp_city_stage(Model):
    _name = 'supp.city.stage'
    _description = u'Справочник город <=> сотрудник'
    _order = 'name'
    _columns = {
        'name': fields.char(
            'Город',
            size=255,
            required=True,
            select=True),
        'address': fields.char(
            'Адрес',
            size=255,
            select=True),
        'phone': fields.char(
            'Телфон',
            size=255),
        'employees_ids': fields.many2many(
            'hr.employee',
            'hr_employee_supp_ink_rel',
            'supp_ink_id',
            'hr_employee_id',
            string='Сотрудники'),
    }

supp_city_stage()


class SupportNotes(Model):
    _name = 'supp.sale.notes'
    _description = u"Квитанции - Обзвон"

    def _get_title(self, cr, uid, ids, field_name, field_value, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            date_str = datetime.strptime(record.create_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            au_dt = tzlocal.normalize(date_str).strftime('%Y-%m-%d %H:%M:%S')
            result[record.id] = u"{0:s} {1:s}: {2:s}".format(record.create_uid.name, au_dt, record.name)
        return result

    _columns = {
        'create_uid': fields.many2one('res.users', 'Написал'),
        'create_date': fields.datetime('Дата и время'),
        'supp_id': fields.many2one('supp.sale', 'Квитанция', invisible=True),
        'name': fields.text('Заметка'),
        'title': fields.function(_get_title, type="char", store=True, method=True, string="Сообщение")
    }

    _order = "create_date desc"

    def action_add(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        supp = context.get('supp_id')

        for obj in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, obj.id, {'name': obj.name, 'supp_id': supp})

        return {'type': 'ir.actions.act_window_close'}

SupportNotes()


class SupportTreatment(Model):
    _name = 'supp.treatment'
    _description = u'Support - Обращения'
    _rec_name = 'id'

    def _get_user(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            access = str()
            if record.author_id.user_id.id == uid:
                access += 'u'

            if uid == 1:
                access += 'a'

            val = False
            letter = name[6]
            if letter in access:
                val = True

            res[record.id] = val
        return res

    _columns = {
        'id': fields.integer(
            'Номер обращения',
            size=11,
            select="1",
            readonly=True),
        'create_date': fields.datetime(
            'Дата создания',
            readonly=True),
        'author_id': fields.many2one(
            'hr.employee',
            'Автор',
            readonly=True),
        'fio': fields.char(
            'ФИО клиента',
            size=250,
            required=True,
            states={'set': [('readonly', True)]}),
        'phone': fields.char(
            'Телефон',
            size=250,
            required=True,
            states={'set': [('readonly', True)]}),
        'note': fields.text(
            'Дополнительная информация',
            help="ICQ, e-mail",
            states={'set': [('readonly', True)]}),
        'city_id': fields.many2one(
            'supp.city.stage',
            'Город',
            select="1",
            required=True,
            states={'set': [('readonly', True)]}),
        'category_list': fields.selection(
            (
                ('printer', 'Принтер'),
                ('snpch', 'СНПЧ'),
                ('pzk', 'ПЗК'),
                ('driver', 'Драйвера'),
            ),
            'Категория товара',
            required=True,
            states={'set': [('readonly', True)]}),
        'model': fields.char(
            'Модель',
            size=250,
            states={'set': [('readonly', True)]}),
        'type_list': fields.selection(
            (
                ('streak', 'Полосит'),
                ('not_see_the_cartridge', 'Не видит картридж'),
                ('drops_on_paper', 'Капли (мажет) на бумаге'),
                ('do_not_be_pulling_paper', 'Не захватывает бумагу'),
                ('lit_2_buttons', 'Горит 2 кнопки (вкл. и капля)'),
                ('the_carriage_does_not_respond', 'Каретка ни на что не реагирует'),
                ('paper_jam', 'Пишет "замятие бумаги"'),
                ('double_vision', 'Двоение на бумаге'),
                ('chip', 'Чип'),
                ('ask_service', 'Обращение в сервис'),
                ('emerged_ink', 'Вытекли чернила'),
                ('damaged_ciss', 'Повреждена СНПЧ'),
                ('return_exchange', 'Возврат/обмен'),
                ('withered', 'Засохла ПГ'),
                ('no_on', 'Не включается принтер'),
                ('ask_sale', 'Обращение в отдел продаж'),
                ('general', 'Общие вопросы'),
            ),
            'Тип неисправности',
            required=True,
            states={'set': [('readonly', True)]}),
        'description': fields.text(
            'Описание неисправности',
            states={'set': [('readonly', True)]}),
        'solution': fields.text(
            'Описание решения',
            states={'set': [('readonly', True)]}),
        # Тип решения

        'state': fields.selection(
            (
                ('draft', 'Черновик'),
                ('set', 'Обращение добавлено'),
            ),
            'Статус'),

        'check_a': fields.function(
            _get_user,
            method=True,
            string="Админ",
            type="boolean",
            invisible=True),
        'check_u': fields.function(
            _get_user,
            method=True,
            string="Автор",
            type="boolean",
            invisible=True),
    }

    _defaults = {
        'author_id': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).id,
        'state': 'draft',
        'check_u': True

    }
SupportTreatment()
