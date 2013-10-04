# -*- encoding: utf-8 -*-
__author__ = 'Karbanovich Andrey'

from osv import osv, fields
from notify import notify


class Video(osv.osv):
    _name = "video"
    _description = u'БП video'
    _log_create = True
    _order = 'id desc'

    workflow_name = 'wkf.video'
    _msg_fields = ['id', 'usr_id', 'partner_id']

    _states = {
        'draft': 'Черновик',
        'cancel': 'Отмена',
        'approval_application': 'Согласование заявки',
        'drawing': 'Составление шаблона ТЗ',
        'completion': 'Заполнение ТЗ',
        'approval_tt': 'Согласование ТЗ',
        'signing': 'Подписание договора',
        'contract_cancel': 'Отмена',
        'development': 'Разработка идей',
        'choice': 'Выбор идей',
        'scripting': 'Составление сценария',
        'approval_scenario': 'Согласование сценария',
        'signing_application': 'Подписание приложения к договору',
        'preparation': 'Подготовительные работы к разработке проекта',
        'approval': 'Согласование',
        'work': 'Работа над проектом',
        'assertion': 'Утверждение заказчиком',
        'project_cancel': 'Отмена',
        'transmission': 'Передача проекта',
        'transferred': 'Проект передан'
    }

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
                group_work = self.pool.get('res.groups').search(cr, 1, [('name', 'in', ('Продажи / Менеджер по работе с партнерами', 'Продажи / Менеджер по развитию партнеров', 'Продажи / Руководитель по развитию партнеров', 'Продажи / Руководитель по работе с партнерами'))])
                users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_work)], order='id')
                if uid in users_work or data.responsible_id.id == uid:
                    access += 'm'

                group_head = self.pool.get('res.groups').search(cr, 1, [('name', 'in', ('Руководители продающих направлений', 'Продажи / Руководитель по развитию партнеров', 'Продажи / Руководитель по работе с партнерами'))])
                users_head = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_head)], order='id')
                if uid in users_head:
                    access += 'h'

                group_head = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Видеостудия')])
                users_head = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_head)], order='id')
                if uid in users_head:
                    access += 'v'
                val = False

                letter = name[6]

                if letter in access:
                    val = True
                res[data.id] = val
        return res

    def onchange_partner(self, cr, uid, ids, field_name, context=None):
        res = {}
        autor_part = {}
        if field_name:
            rez = self.pool.get('crm.lead').search(cr, uid, [('partner_id.id', '=', field_name)], limit=1)
            print "Rez: %s" % rez
            if rez:
                autor_part = self.pool.get('crm.lead').read(cr, uid, rez, ['user_id'])[0]
            if autor_part:
                res['responsible_id'] = autor_part['user_id']
        return {'value': res}

    _columns = {
        'name': fields.char("Name", size=100),
        'state': fields.selection(zip(_states.keys(), _states.values()), 'Статус', size=50, readonly=True),
        #'state': fields.char('Статус', size=50, readonly=True),
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True, select=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', select=True),
        'responsible_id': fields.many2one('res.users',
                                          'Менеджер по работе',
                                          select=True
                                          ),

        'product_type': fields.selection(
            [
                ('commercial', 'Рекламный ролик'),
                ('hidden', 'Скрытая реклама'),
                ('virus', 'Вирусное видео'),
                ('social', 'Социальная реклама'),
                ('presentation', 'Презентационный фильм'),
                ('fashion', 'Имиджевый ролик'),
                ('appeal', 'Обращение, поздравление'),
                ('instruction', 'Видео-инструкция'),
                ('banner', 'Видео-баннер'),
                ('character', 'Виртуальный персонаж'),
                ('animation', 'Анимация'),
                ('review', 'Видео-обзор'),
            ], "Вид создаваемого продукта"),
        'budget': fields.char('Предполагаемый бюджет', size=200),
        'template_file': fields.many2one('attach.files', 'Шаблон ТЗ'),
        'completion_tt_file': fields.many2one('attach.files', 'Заполненное ТЗ'),
        'comment_rework': fields.text('Комментарий по доработке ТЗ'),
        'contract_date': fields.date('Дата подписания договора'),
        'variant_ids': fields.one2many('video.variants', 'video_id', 'Варианты идей'),
        #'idea_file': fields.many2one('attach.files', 'Выбранная идея'),
        'idea_file': fields.char('Выбранная идея', size=250),
        'comment_rework_idea': fields.text('Комментарий по доработке идей'),
        'scenario_file': fields.many2one('attach.files', 'Сценарий для согласования'),
        #'agreed_scenario_file': fields.many2one('attach.files', 'Согласованный сценарий'),
        'agreed_scenario_file': fields.char('Утвержденный сценарий', size=250),
        'comment_rework_scenario': fields.text('Комментарий по доработке сценария'),
        #'application_date': fields.date('Дата подписания приложения к договору'),
        'application_date_ids': fields.one2many('video.applications', 'video_id', 'Приложения к договору'),
        'param_ids': fields.one2many('video.params', 'video_id', 'Параметры создаваемого продукта'),
        #'selected_param_file': fields.many2one('attach.files', 'Выбранные параметры'),
        'selected_param_file': fields.text('Выбранные параметры'),
        'comment_rw': fields.text("Комментарий по доработке"),
        'test_url': fields.char("Тестовая ссылка на готовый продукт", size=250),
        'payment_ids': fields.one2many('video.payment', 'video_id', 'Оплаты'),
        'comment_work': fields.text("Комментарий по выполненой работе"),
        'real_url': fields.char("Реальная ссылка на готовый продукт", size=250),

        'history_ids': fields.one2many('video.history', 'video_id', 'История переходов', readonly=True),

        'check_m': fields.function(_check_access,
                                   method=True,
                                   string="Менеджеры 2 и 3",
                                   type="boolean",
                                   invisible=True),
        'check_v': fields.function(_check_access,
                                   method=True,
                                   string="Ас. руководителя",
                                   type="boolean",
                                   invisible=True),
        'check_h': fields.function(_check_access,
                                   method=True,
                                   string="Рук. продающего подразделения",
                                   type="boolean",
                                   invisible=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'state': 'draft',
        'name': 'test',
    }

    def workflow_setter(self, cr, uid, ids, state='draft'):
        return self.write(cr, uid, ids, {'state': state})

    @notify.msg_send(_name)
    def write(self, cr, user, ids, values, context=None):
        data = self.browse(cr, user, ids)[0]

        next_state = values.get('state', False)
        state = data.state

        error = ''
        if next_state and next_state != state:
            #  if state == '' and next_state == '':
            #  if not data. and not values.get('', False):
            #print "State: {0} -> Next state: {1}".format(state, next_state)

            #  draft -> cancel
            #  draft -> approval_application
            if state == 'draft' and next_state == 'approval_application':
                if not data.partner_id and not values.get('partner_id', False):
                    error += " Выберите партнера; "
                #  Сайты

            #  approval_application -> draft
            if state == 'approval_application' and next_state == 'draft':
                if not data.comment_rw and not values.get('comment_rw', False):
                    error += " Введите комментарий по доработке"
            #  approval_application -> drawing

            #  drawing -> completion
            if state == 'drawing' and next_state == 'completion':
                if not data.template_file and not values.get('template_file', False):
                    error += "Вложите шаблон ТЗ"

            #  completion -> approval_tt
            if state == 'completion' and next_state == 'approval_tt':
                if not data.completion_tt_file and not values.get('completion_tt_file', False):
                    error += " Вложите заполненное ТЗ; "
                if not data.product_type and not values.get('product_type', False):
                    error += " Выберите вид создаваемого продукта; "

            #  approval_tt -> completion
            if state == 'approval_tt' and next_state == 'completion':
                if not data.template_file and not values.get('template_file', False):
                    error += "Вложите шаблон ТЗ; "
                if not data.comment_rework and not values.get('comment_rework', False):
                    error += " Введите комментарий по доработке ТЗ"

            #  approval_tt -> signing
            if state == 'approval_tt' and next_state == 'signing':
                if not data.completion_tt_file and not values.get('completion_tt_file', False):
                    error += " Вложите заполненное ТЗ; "

            #  signing -> contract_cancel
            #  signing -> development
            if state == 'signing' and next_state == 'development':
                if not data.contract_date and not values.get('contract_date', False):
                    error += " Введите дату подписания договора"

            #  development -> choice
            if state == 'development' and next_state == 'choice':
                if not data.variant_ids:
                    error += "Заполните варианты идей"

            #  choice -> development
            if state == 'choice' and next_state == 'development':
                if not data.comment_rework_idea and not values.get('comment_rework_idea', False):
                    error += "Введите комментарий по доработке идей"

            #  choice -> scripting
            if state == 'choice' and next_state == 'scripting':
                if not data.idea_file and not values.get('idea_file', False):
                    error += "Вложите идею"

            #  scripting -> approval_scenario
            if state == 'scripting' and next_state == 'approval_scenario':
                if not data.scenario_file and not values.get('scenario_file', False):
                    error += "Вложите сценарий"

            #  approval_scenario -> scripting
            if state == 'approval_scenario' and next_state == 'scripting':
                if not data.comment_rework_scenario and not values.get('comment_rework_scenario', False):
                    error += "Введите комментарий по доработке идей"

            #  approval_scenario -> signing_application
            if state == 'approval_scenario' and next_state == 'signing_application':
                if not data.agreed_scenario_file and not values.get('agreed_scenario_file', False):
                    error += "Вложите утвержденный сценарий"

            #  signing_application -> preparation
            if state == 'signing_application' and next_state == 'preparation':
                if not data.application_date_ids:
                    error += "Введите дату подписания приложения к договору"

            #  preparation -> approval
            if state == 'preparation' and next_state == 'approval':
                if not data.param_ids:
                    error += "Заполните параметры создаваемого продукта"

            #  approval -> preparation
            if state == 'approval' and next_state == 'preparation':
                if not data.param_ids:
                    error += "Заполните параметры создаваемого продукта"

            #  approval -> work
            if state == 'approval' and next_state == 'work':
                if not data.selected_param_file and not values.get('selected_param_file', False):
                    error += "Введите выбранные параметры"

            #  work -> assertion
            if state == 'work' and next_state == 'assertion':
                if not data.test_url and not values.get('test_url', False):
                    error += "Введите тестовую ссылку"

            #  assertion -> work
            if state == 'assertion' and next_state == 'work':
                if not data.test_url and not values.get('test_url', False):
                    error += "Введите тестовую ссылку"

            #  assertion -> project_cancel
            if state == 'assertion' and next_state == 'project_cancel':
                pass

            #  assertion -> transmission
            if state == 'assertion' and next_state == 'transmission':
                if not data.comment_work and not values.get('comment_work', False):
                    error += " Введите комментарий по выполненой работе; "
                if not data.payment_ids:
                    error += " Заполните оплаты; "

            #  transmission -> transferred
            if state == 'transmission' and next_state == 'transferred':
                if not data.real_url and not values.get('real_url', False):
                    error += "Введите реальную ссылку"

            if error:
                raise osv.except_osv("Video", error)

            values.update({'history_ids': [(0, 0, {
                'usr_id': user,
                'state': self._states[next_state],
                'state_id': next_state
            })]})
            self.log(cr, user, data.id, "test change state in video")
        self.log(cr, user, data.id, "test save without change state in video")
        return super(Video, self).write(cr, user, ids, values, context)

    def copy(self, cr, uid, id, default=None, context=None):
        default['history_ids'] = None
        return super(Video, self).copy(cr, uid, id, default, context)

    def send_message(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids)[0]
        request = self.pool.get('res.request')
        message_text = "{0}".format(data.partner_id)
        message = {
            'body': message_text,
            'name': unicode("VIDEO: надо показать партнеру", "utf-8"),
            'state': 'waiting',
            'act_from': uid,
            'active': True,
            'act_to': data.responsible_id.id
        }

        request.create(cr, uid, message)
        return True


Video()


class VideoVariant(osv.osv):
    _name = 'video.variants'
    _description = u'VIDEO - Варианты идей'
    _log_create = True

    _columns = {
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.many2one('attach.files', 'Файл'),
        'video_id': fields.many2one('video', 'Video', invisible=True),
    }


VideoVariant()


class VideoParams(osv.osv):
    _name = 'video.params'
    _description = u'VIDEO - Параметры создаваемого продукта'
    _log_create = True

    _columns = {
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.many2one('attach.files', 'Файл'),
        'video_id': fields.many2one('video', 'Video', invisible=True),
        }


VideoParams()


class VideoApplications(osv.osv):
    _name = 'video.applications'
    _description = u'VIDEO - Приложения к договору'
    _log_create = True

    _columns = {
        'name': fields.datetime('Дата подписания'),
        'file': fields.many2one('attach.files', 'Файл'),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'video_id': fields.many2one('video', 'Video', invisible=True),
        }


VideoApplications()


class VideoPayment(osv.osv):
    _name = 'video.payment'
    _description = u'VIDEO - Оплаты'
    _log_create = True

    _columns = {
        'name': fields.datetime('Дата оплаты'),
        'pay_currency': fields.many2one('partner.currency', 'Валюта оплаты'),
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'summ_pay': fields.float('Сумма оплаты'),
        'summ_pay_$': fields.float('Сумма оплаты в $'),
        'sum_enrollment_$': fields.float('Сумма к зачислению в $'),
        'video_id': fields.many2one('video', 'Video', invisible=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
    }

VideoPayment()


class VideoHistory(osv.osv):
    _name = 'video.history'
    _description = u'Video - История переходов'
    _log_create = True
    _log_access = True
    _order = "create_date desc"
    _rec_name = 'state'

    _columns = {
        'usr_id': fields.many2one('res.users', 'Перевел'),
        'state': fields.char('На этап', size=65),
        'video_id': fields.many2one('video', 'VIDEO', invisible=True),
    }


VideoHistory()
