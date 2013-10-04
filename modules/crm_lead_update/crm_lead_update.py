# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import re
from openerp import tools
from openerp.osv import osv, fields
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


def format_date_tz(date, tz=None):
    if not date:
        return 'n/a'
    f = tools.DEFAULT_SERVER_DATETIME_FORMAT
    return tools.server_to_local_timestamp(date, f, f, tz)


class crm_services_rel_stage(osv.osv):
    """ CRM Lead services stage rel """
    _name = "crm.services.rel.stage"

    _rec_name = 'comment'
    _columns = {
        'service_id': fields.many2one('brief.services.stage', u'Услуга'),
        'crmlead_ids': fields.many2one(
            'crm.lead',
            u'Кандидат',
            invisible=True,
            ondelete='cascade'
        ),
        'comment': fields.text(u'Комментарий'),
        'partner_id': fields.many2one('res.partner', u'Партнер', inbisible=True)
    }


crm_services_rel_stage()


class crm_case_categ(osv.osv):
    """ Category of Case """
    _name = "crm.case.categ"
    _description = "Category of Case"
    _inherit = "crm.case.categ"
    _order = "name"

    #'|',('responsible_user','=',user.id), ('user_id','=',user.id)
    _columns = {
        'responsible_users': fields.many2many(
            'res.users',
            'res_user_crm_case_categ_rel',
            'case_id',
            'usr_id',
            string=u'Доступно'),
    }


crm_case_categ()


class crm_source_stage(osv.osv):
    """ CRM Lead source stage """
    _name = "crm.source.stage"

    _columns = {
        'name': fields.char(u'Название источника', size=255, select=True),
        'section_id': fields.many2one('crm.case.section', u'Отдел продаж'),
    }


crm_source_stage()


class crm_type_base(osv.osv):
    """ CRM Lead type base (hot/cold) """
    _name = "crm.type.base"
    _val = [
        ('cold', 'Холодный контакт'),
        ('hot', 'Теплый контакт'),
    ]
    _columns = {
        'name': fields.many2one('res.groups', u'Группа', required=True),
        'partner_type': fields.selection(_val, u'Тип базы', required=True),
    }


crm_type_base()


class CommunicationType(osv.osv):
    """
        Хранит Способы коммуникации для CommunicationHistory
    """
    _name = 'crm.communication.type'
    _description = 'Communication Type'

    _columns = {
        'name': fields.char(u'Способ общения', size=250),
    }


CommunicationType()


class CommunicationDocuments(osv.osv):
    """
        Хранит имена отправленных документов для CommunicationHistory
    """
    _name = 'crm.communication.documents'
    _description = 'Communication Documents'

    _columns = {
        'name': fields.char(u'Документ', size=250),
    }


CommunicationDocuments()


class CommunicationHistory(osv.osv):
    """
        Объект для хранения коммуникаций с кандидатом
            Связи one2many - crm.lead
                           - res.partner
    """
    _name = 'crm.communication.history'
    _description = 'Communication History'

    _columns = {
        'lead_id': fields.many2one('crm.lead', u'Кандидат', invisible=True),
        'partner_id': fields.many2one('res.partner', u'Партнер', invisible=True),
        'create_date': fields.datetime(u'Дата', readonly=True),
        'type': fields.many2one('crm.communication.type', u'Способ'),
        'length': fields.char(u'Продолжительность', size=250),
        'point': fields.char(u'Суть', size=250),
        'documents': fields.many2one('crm.communication.documents', u'Документы'),
        'result': fields.char(u'Результат', size=250),
        'note': fields.char(u'Примечание', size=250),
        'user_id': fields.many2one('res.users', u'Отв.', readonly=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }


CommunicationHistory()


class crm_patner_product_type(osv.osv):
    _name = 'crm.patner.product.type'
    _columns = {
        'name': fields.char(u'Тип товара', size=256),
    }


crm_patner_product_type()


class crm_patner_product(osv.osv):
    _name = 'crm.patner.product'
    _columns = {
        'name': fields.many2one('crm.patner.product.type', u'Тип товара'),
        'description': fields.char(u'Наименование', size=256),
        'comment': fields.text(u'Коментарий'),
        'crm_lead': fields.many2one('crm.lead', u'Кандидат'),
        'res_partner': fields.many2one('res.partner', u'Партнер'),
    }


crm_patner_product()


class crm_lead_failure_cause(osv.osv):
    _name = 'crm.lead.failure.cause'
    _description = u"Причины отказа"
    _columns = {
        'name': fields.char(u"Причина", size=256)
    }


crm_lead_failure_cause()


class res_partner_bank(osv.osv):
    _name = "res.partner.bank"
    _inherit = "res.partner.bank"
    _columns = {
        'lead_id': fields.many2one('crm.lead', u'Кандидат', select=True),
    }


res_partner_bank()


class LeadNotes(osv.osv):
    _name = 'crm.lead.notes'
    _description = u"Заметки кандидатов"

    def _get_title(self, cr, uid, ids, field_name, field_value, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            date_str = datetime.strptime(record.create_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            au_dt = tzlocal.normalize(date_str).strftime('%Y-%m-%d %H:%M:%S')
            result[record.id] = "%s %s: %s" % (record.create_uid.name, au_dt, record.name)
        return result

    _columns = {
        'create_uid': fields.many2one('res.users', u'Написал'),
        'create_date': fields.datetime(u'Дата и время'),
        'lead_id': fields.many2one('crm.lead', u'Кандидат', invisible=True),
        'partner_id': fields.many2one('res.partner', u'Партнер', invisible=True),
        'name': fields.text(u'Заметка'),
        'title': fields.function(_get_title, type="char", store=True, method=True, string=u"Сообщение"),
        'type': fields.selection(
            (
                ('message', 'message'),
                ('skk', 'skk')
            ), 'Тип'
        )
    }

    _order = "create_date desc"

    def action_add(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        lead = context.get('lead_id')
        partner = context.get('partner_id')

        for obj in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, obj.id, {'name': obj.name, 'lead_id': lead, 'partner_id': partner, 'type': context.get('type')})

        return {'type': 'ir.actions.act_window_close'}

    def check_len(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, ['name']):
            if len(record['name']) < 30:
                return False
        return True

    _constraints = [(check_len, u'Сообщение должно быть более 30 символов.', [u'Заметка'])]

LeadNotes()


class TransferHistory(osv.osv):
    _name = 'transfer.history'
    _description = u'Lead/Partner - История переприсвоение карточки'
    _log_create = True
    _order = "create_date desc"

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'name': fields.many2one('res.users', 'На кого переприсвоили'),
        'create_date': fields.datetime('Дата', readonly=True),
        'lead_id': fields.many2one('crm.lead', 'Кандидат', invisible=True),
    }

TransferHistory()


class crm_lead(osv.osv):
    """ CRM Lead Case """
    _name = "crm.lead"
    _description = u"Кандидаты"
    _inherit = "crm.lead"

    _order = "priority, create_date desc"

    _val_type_base = lambda self, cr, uid, context: self.pool.get('crm.type.base')._val

    def transfer_lead(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        users = self.pool.get('res.users')
        brief_pool = self.pool.get('brief.main')
        brief_groups = self.pool.get('brief.manager.groups')

        if data.partner_type == 'cold':
            manager_id = brief_groups.search(cr, 1, [('manager_first_lvl_ids', 'in', [data.user_id.id])])

            if manager_id:
                manager = brief_groups.read(cr, 1, manager_id[0], ['manager_second_lvl_id'])
                values = {
                    'user_id': manager['manager_second_lvl_id'][0],
                    'section_id': users.browse(cr, uid, manager['manager_second_lvl_id'][0]).context_section_id.id,
                    'partner_type': 'hot',
                    'round_datetime': datetime.now(pytz.utc)
                }
                self.write(cr, uid, ids[0], values)

                b_ids = brief_pool.search(cr, uid, [('cand_id', '=', ids[0])])
                if b_ids:
                    brief_pool.write(cr, uid, b_ids, {'responsible_user': manager['manager_second_lvl_id'][0]})

        return ids

    def add_note(self, cr, uid, ids, context=None):
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'CRM Note'), ('model', '=', self._name)])
        return {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'crm.lead.notes',
            'name': 'Добавление заметки',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': {
                'lead_id': ids[0],
            },
            'target': 'new',
            'nodestroy': True,
        }

    #  TODO check_access
    def _check_permissions(self, cr, uid, ids, field_name, arg, context=None):
        """
            Поле необходимо для динамического отслеживания роли пользователя в записи
                и дальнейшего контроля прав
        """
        res = {}
        data = self.browse(cr, uid, ids)
        for field in data:
            user_data = self.pool.get('res.users').browse(cr, uid, uid)
            manager_groups = [unicode("Продажи / Руководитель по работе с партнерами", "utf-8"),
                              unicode("Продажи / Руководитель по привлечению партнеров", "utf-8")]
            for group in user_data.groups_id:
                if group.name in manager_groups:
                    res[field.id] = "Director"
        return res

    # TODO посомтреть что за муть с вложенными форами
    def _get_type_base(self, cr, uid, context=None):
        res = 'cold'
        obj_type_base = self.pool.get('crm.type.base')
        user_data = self.pool.get('res.users').browse(cr, uid, uid)
        manager_groups = obj_type_base.browse(cr, uid, obj_type_base.search(cr, uid, []))
        for ugroup in user_data.groups_id:
            for mgroup in manager_groups:
                if ugroup.id == mgroup.name.id:
                    res = mgroup.partner_type
        return res

    # TODO проверить где используется и как
    def to_call(self, cr, *args):
        now = datetime.now(pytz.utc)
        d = timedelta(hours=4)
        later = now + d

        ids = self.search(cr, 1,
                          [
                              ('next_call', '>', now.strftime("%d/%m/%y %H:%M")),
                              ('next_call', '<=', later.strftime("%d/%m/%y %H:%M"))
                          ],
                          order='next_call')
        data = self.browse(cr, 1, ids)

        if data:
            for item in data:
                print "%s | %s | %s" % (
                    item.name.ljust(30, ' '), item.responsible_user.name.ljust(30, ' '), item.next_call.rjust(20, ' '))
        else:
            print u"Некому звонить :( "

    #
    def _phone_default(self, cr, uid, ids, field_name, field_value, arg, context=None):
        records = self.browse(cr, uid, ids, context=context)
        result = {}
        tel_obj = self.pool.get('tel.reference')
        for r in records:
            phones = tel_obj.search(cr, uid, [('crm_lead_id', '=', r.id)])
            if phones:
                for p in phones:
                    phone = tel_obj.browse(cr, uid, p, context=context)
                    result[r.id] = phone.phone
                    break
            else:
                result[r.id] = ''
        return result

    _columns = {
        'incident': fields.char(u'Инцидент', size=255),
        'source': fields.many2one('crm.source.stage', u'Источник'),
        'email_2': fields.char(u'Эл.Почта (2)', size=255),
        'site_url_2': fields.char(u'Сайт кандидата (2)', size=255),
        'services_ids': fields.one2many('crm.services.rel.stage', 'crmlead_ids', u'Услуги'),

        'responsible_user': fields.many2one('res.users', u'Ответственный'),
        'partner_type': fields.selection(_val_type_base, u'Тип базы', readonly=True),

        'permissions': fields.function(
            _check_permissions,
            type="char",
            obj="crm.lead",
            method=True,
            string=u"Права доступа"
        ),
        'site_url_1': fields.char(u'Сайт кандидата', size=255),
        'next_call': fields.datetime(u'Дата следующего звонка'),
        'delay_call_task': fields.float(u'Время для задания звонка', digits=(1, 2)),
        'first_call': fields.datetime(u'Дата первого звонка'),
        'company_type': fields.selection(
            [
                ('inksystem', 'INKSYSTEM'),
                ('contact', 'Контакт-центр'),
                ('upsale', 'UpSale'),
                ('eu', 'ЕС'),
            ], u'Кандидат компании'),
        'state_ec': fields.char(u'Область', size=250),
        'country_ec': fields.char(u'Страна', size=250),
        'calles': fields.one2many('crm.phonecall', 'opportunity_id', string=u'Звонки'),
        'note_ids': fields.one2many(
            'crm.lead.notes',
            'lead_id',
            u'Заметки'
        ),
        'activity': fields.char(u'Сфера деятельности', size=250),
        'cand_type': fields.selection([('pers', 'Частное лицо'), ('firm', 'Фирма')], u'Тип кандидата'),
        'sale_type': fields.selection([('w', 'Опт'), ('r', 'Розница')], u'Тип продаж'),
        'skype': fields.char('Skype', size=250),
        'msn': fields.char('MSN', size=250),
        'yahoo': fields.char('Yahoo', size=250),
        'icq': fields.char('ICQ', size=250),
        'gg': fields.char('GG', size=250),
        'comm_ids': fields.one2many('crm.communication.history', 'lead_id', string=u"История общения"),
        'product_id': fields.one2many('crm.patner.product', 'crm_lead', string=u"Товары"),
        'comm_next_call': fields.char(u'Комментарий к следующему звонку', size=250),
        'round_datetime': fields.datetime(u'Дата распределения'),

        'last_comment': fields.related('note_ids', 'title', type='char', size=128, string=u'Комментарий'),
        'last_call': fields.related('calles', 'date', type='datetime', size=128, string=u'Дата последнего звонка'),
        'phone_default': fields.related('phone_ids', 'phone', type='char', size=128, string=u'Телефон'),

        'failure_cause_id': fields.many2one('crm.lead.failure.cause', u'Причина отказа'),
        'another_failure_cause': fields.char(u'Другой вариант отказа', size=250),
        'bank_ids': fields.one2many('res.partner.bank', 'lead_id', string=u"Реквизиты кандидата"),
        'transfer_ids': fields.one2many('transfer.history', 'lead_id', 'История переприсвоения'),
    }

    _defaults = {
        'responsible_user': lambda self, cr, uid, context: uid,
        'partner_type': lambda self, cr, uid, context: self._get_type_base(cr, uid, context),
        'delay_call_task': lambda *a: 0.5,
    }

    _view_type = 'form'

    def _check_unique_insesitive(self, cr, uid, ids, context=None):
        for self_obj in self.browse(cr, 1, ids, context):
            if self.search(cr, 1, [('name', '=', self_obj.name), ('id', '!=', self_obj.id)], context):
                return False
            return True

    _constraints = [
        #(
        #    _check_unique_insesitive,
        #    'Error: Поле "Основной сайт"/"Кандидат" должно быть уникальным!',
        #    ['name']
        #)
    ]

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        self._view_type = view_type
        return super(crm_lead, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=None):
        i = 0
        for item in args:
            if 'name' in item:
                args.append(('name', args.pop(i)[1], re.sub("\s*\n\s*", ' ', item[2].strip())))
            i += 1

        if self._view_type == 'calendar':
            user_data = self.pool.get('res.users').browse(cr, uid, uid)
            for group in user_data.groups_id:
                if group.name == u'Продажи / Менеджер по привлечению партнеров':
                    args.append(('partner_type', '=', 'cold'))
        return super(crm_lead, self).search(cr, uid, args, offset, limit, order, context, count)

    def write(self, cr, uid, ids, values, context=None):
        if values.get('stage_id', False) and values['stage_id'] == 41:
            values['next_call'] = datetime.now(pytz.utc) + timedelta(days=60)

        return super(crm_lead, self).write(cr, uid, ids, values, context)

crm_lead()
