# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify

__author__ = 'Karbanovich Andrey'


class BriefMeeting(Model):
    _name = "brief.meeting"
    _description = u'Бриф на встречу'
    _log_create = True
    _rec_name = 'state'
    _order = 'date desc'

    workflow_name = 'brief.meeting'

    def _get_group(self, cr):
        return self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Бриф на встречу / Менеджер Москвы')])

    _states = {
        'draft': 'Черновик',
        'cancel': 'Отмена',
        'scheduled': 'Встреча назначена',
        'canceled': 'Отмена встречи',
        'held': 'Встреча проведена',
        'reschedule': 'Необходимо перенести встречу'
    }

    def _get_sites(self, cr, uid, ids, field_name, arg, context=None):
        res = {}

        data = self.browse(cr, uid, ids)
        for record in data:
            sites = []
            if record.partner_id or record.candidate_id:
                if record.partner_id:
                    sites = [site.id for address in record.partner_id.address for site in address.site_ids]
            res[record.id] = sites

        return res

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        if ids:
            data_ids = self.browse(cr, uid, ids, context)

            for data in data_ids:
                access = str()

                #  Менеджеры 2 и 3
                group_work = self.pool.get('res.groups').search(
                    cr,
                    1,
                    [
                        ('name', 'in', (
                            'Продажи / Менеджер по работе с партнерами',
                            'Продажи / Менеджер по развитию партнеров',
                            'Продажи / Руководитель по развитию партнеров',
                            'Продажи / Руководитель по работе с партнерами',
                            'Продажи / Менеджер по привлечению партнеров',
                            'Продажи / Руководитель по привлечению партнеров',
                        ))
                    ])
                users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_work)], order='id')
                if uid in users_work:
                    access += 'm'

                #  Менеджер Москвы
                if data.responsible_id.id == uid:
                    access += 'r'

                val = False

                letter = name[6]

                if letter in access:
                    val = True
                res[data.id] = val
        return res

    _columns = {
        'state': fields.selection(
            zip(_states.keys(), _states.values()),
            'Статус',
            readonly=True,
            help='Поле отображает текущий этап Брифа.'),
        'usr_id': fields.many2one(
            'res.users',
            'Автор',
            readonly=True,
            select=True,
            help='Автор (менеджер продаж).'),
        'partner_id': fields.many2one(
            'res.partner',
            'Партнер',
            select=True,
            help='Партнер по которому создается Бриф.'),
        'candidate_id': fields.many2one(
            'crm.lead',
            'Кандидат',
            select=True,
            help=''),
        'responsible_id': fields.many2one(
            'res.users',
            'Ответственный',
            select=True,
            domain="[('groups_id','in',[131])]",
            help='Сотрудник ответственный за проведение встречи.'
        ),
        'line_of_activity': fields.char(
            "Направление деятельности",
            size=250,
            help='Текстовое, необязательное поле. В случае необходимости указывается направление деятельности Партнера'
        ),

        'site_partner_ids': fields.function(
            _get_sites,
            type="one2many",
            obj="res.partner.address.site",
            method=True,
            string="Сайты",
            help='Таблица сайтов выбранного Партнера. Заполняется на этапе создания Брифа'
        ),

        'venue': fields.selection(
            [
                ('our', 'Встреча в нашем офисе'),
                ('client', 'Встреча в офисе клиента')
            ],
            'Место проведения встречи',
            help='Выпадающий список. Обязательное к заполнению на этапе создания Брифа'
        ),
        'date': fields.datetime(
            'Дата/время встречи',
            help='Дата/время встречи'),
        'duration': fields.float(
            'Продолжительность встречи',
            digits=(1, 2)),
        'participant_ids': fields.one2many(
            'brief.meeting.participants',
            'meeting_id',
            'Участники',
            help='Участники встречи со стороны Партнера. Заполняется на этапе создания Брифа'),
        'primary_goal': fields.text(
            'Основная цель',
            help='Текстовое поле. Обязательное к заполнению на этапе создания Брифа'),
        'additional_goals': fields.text(
            'Дополнительные цели',
            help='Текстовое поле. Обязательное к заполнению на этапе создания Брифа'),
        #  Адрес
        'city': fields.char(
            'Город',
            size=200,
            help='Текстовое поле. Обязательное к заполнению на этапе создания Брифа'),
        'metro': fields.char(
            'Ст. метро',
            size=200,
            help='Текстовое поле. Не обязательное к заполнению на этапе создания Брифа'),
        'street': fields.char(
            'Улица',
            size=250,
            help='Текстовое поле. Обязательное к заполнению на этапе создания Брифа'),
        'house': fields.char(
            'Дом',
            size=20,
            help='Номер дома. Обязательное к заполнению на этапе создания Брифа'),
        'housing': fields.char(
            'Корпус',
            size=20,
            help='Номер корпуса, заполняется в случае необходимости.'),
        'apartment': fields.char(
            'Квартира/офис',
            size=20,
            help='Номер квартиры, офиса. Заполняется в случае необходимости.'),
        'mkad': fields.boolean(
            'За МКАДом',
            help='Галочка выставляется, в случае проведения встречи за МКАДом.\n'
                 'Данная опция увеличивает время для встречи на 1 час.'),
        'document_ids': fields.many2many(
            'attach.files',
            'brief_meeting_doc_attachment_rel',
            'brief_id',
            'attachment_id',
            'Необходимые документы',
            #domain=[('res_model', '=', 'brief.main')],,
            help='Перечень необходимых документов для проведения встречи.'
        ),
        'short_description': fields.text(
            'Краткое описание переговоров',
            help='Текстовое поле, заполняется в случае необходимости'),
        'first_date': fields.datetime(
            'Дата первого общения',
            help='Дата, поле необязательное к заполнению'),

        'comment_ids': fields.one2many(
            'brief.meeting.comments',
            'meeting_id',
            'Комментарии',
            help='Таблица для добавления комментариев в случае необходимости.'),
        'need_to_get_ids': fields.one2many(
            'brief.meeting.need_get',
            'meeting_id',
            'Что необходимо получить',
            help='Перечень документов (информации), которые необходимо получить во время встречи.'
                 ' Обязательное к заполнению на этапе создания Брифа'
        ),
        'need_to_transfer_ids': fields.one2many(
            'brief.meeting.need_transfer',
            'meeting_id',
            'Что необходимо передать',
            help='Перечень документов (информации), которые необходимо передать во время встречи.'
                 ' Обязательное к заполнению на этапе создания Брифа'
        ),
        'contact_ids': fields.one2many(
            'brief.meeting.contacts',
            'meeting_id',
            'Контактные лица',
            help='Перечень контактных лиц со стороны Партнера. Заполняется в случае необходимости'),
        'cancel_reasons': fields.text(
            'Причины отмены',
            help='Текстовое поле. Обязательное к заполнению при переводе Брифа на этап "Встреча отменена"'),
        'reschedule_reasons': fields.text(
            'Причины переноса встречи',
            help='Текстовое поле. Обязательное к заполнению при переводе Брифа на этап "Встреча перенесена"'),
        'canceled_reasons': fields.text(
            'Причины отмены встречи',
            help='Текстовое поле. Обязательное к заполнению при переводе Брифа на этап "Встреча отменена"'),
        'result': fields.text(
            'Результат проведения встречи',
            help='Текстовое поле. Обязательное к заполнению при переводе Брифа на этап "Встреча проведена"'),

        'history_ids': fields.one2many(
            'brief.meeting.history',
            'meeting_id',
            'История переходов',
            help='Записывается история смены этапов Брифа. Заполняется автоматически.'),

        'check_m': fields.function(
            _check_access,
            method=True,
            string="Проверка на менеджера",
            type="boolean",
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string="Проверка на ответственного",
            type="boolean",
            invisible=True
        ),
        'from': fields.char("from", size=10),
        'budget_ye': fields.float('Бюджет встречи в у.е.', digits=(10, 2), required=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'candidate_id': lambda self, cr, uid, context: context.get('candidate_id', False),
        'partner_id': lambda self, cr, uid, context: context.get('partner_id', False),
        'from': lambda self, cr, uid, context: context.get('from', False),
        'state': 'draft',
    }

    def onchange_venue(self, cr, uid, ids, venue, context=None):
        res = {}
        if venue == 'our':
            res['city'] = "Москва"
            res['metro'] = "Cмоленская"
            res['street'] = "Новый Арбат"
            res['house'] = "21"
            res['apartment'] = "1604"
            res['mkad'] = False
        else:
            res['city'] = ""
            res['metro'] = ""
            res['street'] = ""
            res['house'] = ""
            res['apartment'] = ""

        return {'value': res}

    def workflow_setter(self, cr, uid, ids, state='draft'):
        return self.write(cr, uid, ids, {'state': state})

    def create(self, cr, user, vals, context=None):
        if vals.get('from'):
            vals['from'] = None
        if vals.get('partner_id'):
            self.pool.get('res.partner').write(cr, user, [vals['partner_id']], {'partner_base': 'hot'})
        return super(BriefMeeting, self).create(cr, user, vals, context)

    @notify.msg_send(_name)
    def write(self, cr, user, ids, values, context=None):
        if values.get('from'):
            values['from'] = None

        for data in self.browse(cr, user, ids):
            try:
                mkad = values['mkad']
            except:
                mkad = data.mkad

            if mkad:
                values['duration'] = 3
            else:
                values['duration'] = 2

            next_state = values.get('state', False)
            state = data.state

            error = ''
            if next_state and next_state != state:
                #  draft -> cancel
                if state == 'draft' and next_state == 'cancel':
                    pass
                    #if not data.cancel_reasons and not values.get('cancel_reasons', False):
                    #    error += 'Необходимо заполнить причины отмены'
                #  cancel -> draft
                #  draft -> scheduled
                if state == 'draft' and next_state == 'scheduled':
                    if not values.get('partner_id') and not data.partner_id and not values.get('candidate_id', False) and not data.candidate_id:
                        error += " Выберите партнера или кандидата; "
                    if not values.get('line_of_activity', False) and not data.line_of_activity:
                        error += " Введите Направление деятельности; "
                    venue = values['venue'] if values.get('venue', False) else data.venue
                    if venue == 'our':
                        if not data.participant_ids:
                            error += 'Необходимо указать Участников встречи; '

                        if not data.document_ids:
                            error += 'Необходимо указать Необходимые документы; '

                    elif venue == 'client':
                        if not data.contact_ids:
                            error += 'Необходимо указать Контактные лица; '

                        if not data.need_to_get_ids:
                            error += 'Необходимо указать Что необходимо получить; '

                        if not data.need_to_transfer_ids:
                            error += 'Необходимо указать Что необходимо передать; '

                    if not data.primary_goal and values.get('primary_goal', False):
                        error += 'Необходимо указать Основную цель'

                    if not data.additional_goals and values.get('primary_goal', False):
                        error += 'Необходимо указать Дополнительные цели'

                    #if not data.comment_ids:
                    #    error += 'Необходимо внести Комментарии; '

                    if not data.first_date and values.get('first_date', False):
                        error += 'Необходимо указать Дату первого общения'

                    if not data.short_description and values.get('short_description', False):
                        error += 'Необходимо указать Краткое описание переговоров'

                #  scheduled -> canceled
                if state == 'scheduled' and next_state == 'canceled':
                    if not data.canceled_reasons and not values.get('canceled_reasons', False):
                        error += 'Необходимо заполнить причины отмены встречи'
                #  scheduled -> held
                if state == 'scheduled' and next_state == 'held':
                    if not data.result and not values.get('result', False):
                        error += 'Необходимо заполнить результаты проведения встречи'

                #  scheduled -> reschedule
                if state == 'scheduled' and next_state == 'reschedule':
                    if not data.reschedule_reasons and not values.get('reschedule_reasons', False):
                        error += 'Необходимо заполнить причины переноса встречи'
                #  reschedule -> scheduled

                if error:
                    raise osv.except_osv("Brief meeting", error)

                values.update({'history_ids': [(0, 0, {
                    'usr_id': user,
                    'state': self._states[next_state],
                    'state_id': next_state
                })]})

        return super(BriefMeeting, self).write(cr, user, ids, values, context)

    def action_add(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
BriefMeeting()


class BriefMeetingParticipants(Model):
    _name = 'brief.meeting.participants'
    _description = u'Бриф на встречу - Участники'
    _log_create = True

    _columns = {
        'name': fields.char('ФИО', size=255),
        'post': fields.char('Должность', size=255),
        'phone': fields.char('Номер телефона', size=255),
        'car': fields.char('Номер/марка машины', size=255),
        'comment': fields.char('Комментарий', size=255),
        'personality': fields.text('Особенности характера'),
        'meeting_id': fields.many2one('brief.meeting', 'Бриф на встречу', invisible=True),
    }
BriefMeetingParticipants()


class BriefMeetingComments(Model):
    _name = 'brief.meeting.comments'
    _description = u'Бриф на встречу - Комментарии'
    _log_create = True
    _order = "create_date desc"

    _columns = {
        'name': fields.text('Комментарий'),
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'meeting_id': fields.many2one('brief.meeting', 'Бриф на встречу', invisible=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
    }
BriefMeetingComments()


class BriefMeetingHistory(Model):
    _name = 'brief.meeting.history'
    _description = u'Бриф на встречу - История переходов'
    _log_create = True
    _order = "create_date desc"
    _rec_name = 'state'

    _columns = {
        'usr_id': fields.many2one('res.users', 'Перевел'),
        'state': fields.char('На этап', size=65),
        'meeting_id': fields.many2one('brief.meeting', 'Бриф на встречу', invisible=True),
    }
BriefMeetingHistory()


class BriefMeetingNeedTo(Model):
    _name = 'brief.meeting.need_to'
    _description = u'Бриф на встречу - Необходимо получить\передать'
    _log_create = True

    _columns = {
        'name': fields.char('Описание', size=255),
        'type': fields.selection([('get', 'Получить'), ('transfer', 'Передать')], 'Тип', readonly=True),
        'file_id': fields.many2one('attach.files', 'Файл'),
        'meeting_id': fields.many2one('brief.meeting', 'Бриф на встречу', invisible=True),
    }

    _defaults = {
        'type': 'get'
    }
BriefMeetingNeedTo()


class BriefMeetingNeedToGet(Model):
    _name = 'brief.meeting.need_get'
    _description = u'Бриф на встречу - Необходимо получить'
    _log_create = True

    _columns = {
        'name': fields.char('Описание', size=255),
        'file_id': fields.many2one('attach.files', 'Файл'),
        'meeting_id': fields.many2one('brief.meeting', 'Бриф на встречу', invisible=True),
    }
BriefMeetingNeedToGet()


class BriefMeetingNeedToTransfer(Model):
    _name = 'brief.meeting.need_transfer'
    _description = u'Бриф на встречу - Необходимо передать'
    _log_create = True

    _columns = {
        'name': fields.char('Описание', size=255),
        'file_id': fields.many2one('attach.files', 'Файл'),
        'meeting_id': fields.many2one('brief.meeting', 'Бриф на встречу', invisible=True),
    }
BriefMeetingNeedToTransfer()


class BriefMeetingContacts(Model):
    _name = 'brief.meeting.contacts'
    _description = u'Бриф на встречу - Контактные лица'
    _log_create = True

    _columns = {
        'name': fields.char('ФИО', size=255),
        'post': fields.char('Должность', size=255),
        'phone': fields.char('Номер телефона', size=255),
        'comment': fields.char('Комментарий', size=255),
        'meeting_id': fields.many2one('brief.meeting', 'Бриф на встречу', invisible=True),
    }
BriefMeetingContacts()


class res_partner(Model):
    _inherit = "res.partner"

    _columns = {
        'brief_meeting_ids': fields.one2many(
            'brief.meeting',
            'partner_id',
            u'Брифы на встречу'
        ),
    }

    def create_brief_meeting(self, cr, uid, ids, context=None):
        """
            Открывает окно с брифом и переданными данными
        """
        data = False
        if ids:
            action_pool = self.pool.get('ir.actions.act_window')
            action_id = action_pool.search(cr, uid, [('name', '=', 'Создать бриф на встречу ')], context=context)
            if action_id:
                data = action_pool.read(cr, uid, action_id[0], context=context)

                data.update({
                    'nodestroy': True,
                    'context': {
                        'partner_id': ids[0],
                        'from': 'lp'
                    }
                })

        return data

res_partner()
