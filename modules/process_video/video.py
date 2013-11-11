# coding=utf-8
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from notify import notify


STATES = (
    ('coordination', 'Согласование заявки на запуск'),
    ('filling_TK', 'Заполнение ТЗ'),
    ('matching_TK', 'Согласование ТЗ'),
    ('development', 'Разработка идей'),
    ('selection', 'Выбор идеи'),
    ('drawing_up', 'Составление сценария'),
    ('matching_script', 'Согласование сценария'),
    ('signing_application', 'Подписание приложения к договору'),
    ('preparation', 'Подготовительные работы к разработке проекта'),
    ('approval', 'Согласование вариантов'),
    ('work', 'Работа над проектом'),
    ('assertion', 'Утверждение заказчиком'),
    ('transmission', 'Передача проекта'),
    ('finish', 'Проект передан'),
    ('cancel', 'Отмена'),
)


class ProcessVideo(Model):
    _name = 'process.video'
    _inherit = 'process.base'
    _description = u'Процессы - Video'
    _rec_name = 'name'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['responsible_id', 'specialist_id', 'service_head_id'], context):
            access = str()

            #  Менеджер
            if data.get('responsible_id') and data['responsible_id'][0] == uid:
                access += 'a'

            #  Ассистент + Руководитель
            if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', '=', 97)]):
                access += 'm'

            #  Специалисты
            if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', '=', 82)]):
                access += 's'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[data['id']] = val
        return res

    def onchange_work_state(self, cr, uid, ids, work_state, context=None):
        return {'value': {work_state: True}}

    def name_get(self, cr, user, ids, context=None):
        return [
            (
                r['id'],
                "{0}".format(r['name'][1].encode('utf8'),)
            ) for r in self.read(cr, user, ids, ['name'])]

    _columns = {
        'name': fields.char("Рабочее название проекта", size=100),
        'state': fields.selection(STATES, 'статус', readonly=True),

        'history_ids': fields.one2many(
            'process.history',
            'process_id',
            'История',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'report_ids': fields.one2many(
            'process.reports',
            'process_id',
            'Отчеты',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'message_ids': fields.one2many(
            'process.messages',
            'process_id',
            'Переписка по проекту',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),

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
            ], "Вид создаваемого продукта",
            readonly=True,
            states={
                'coordination': [('readonly', False), ('required', True)]
            }),
        'budget': fields.char('Предполагаемый бюджет', size=200),

        'completion_tk_id': fields.many2one(
            'ir.attachment',
            'Заполненное ТЗ',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'completion_tk')],
            context={'process_model': _name, 'tmp_res_model': 'completion_tk'},
            readonly=True,
            states={
                'filling_TK': [('readonly', False), ('required', True)]
            }),
        'comment_rework': fields.text(
            'Комментарий по доработке ТЗ',
            readonly=True,
            states={
                'matching_TK': [('readonly', False)]
            }),

        'variant_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Варианты идей',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'variants')],
            context={'res_model': _name, 'tmp_res_model': 'variants'}),
        'idea_file': fields.char('Выбранная идея', size=250),
        'comment_rework_idea': fields.text('Комментарий по доработке идей'),

        'scenario_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Варианты сценариев',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'scenario')],
            context={'res_model': _name, 'tmp_res_model': 'scenario'}),
        'agreed_scenario_file': fields.char('Утвержденный сценарий', size=250),
        'comment_rework_scenario': fields.text('Комментарий по доработке сценария'),

        'graphic': fields.boolean(
            'Графика',
            readonly=True,
            states={
                'work': [('readonly', False)]
            }),
        'graphic_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Графика для согласования',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'graphic')],
            context={'res_model': _name, 'tmp_res_model': 'graphic'}),
        'agreed_graphic_file': fields.char('Утвержденная графика', size=250),

        'speaker': fields.boolean(
            'Дикторы',
            readonly=True,
            states={
                'work': [('readonly', False)]
            }),
        'speaker_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Дикторы на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'speaker')],
            context={'res_model': _name, 'tmp_res_model': 'speaker'}),
        'agreed_speaker_file': fields.char('Утвержденные дикторы', size=250),

        'actor': fields.boolean(
            'Актеры',
            readonly=True,
            states={
                'work': [('readonly', False)]
            }),
        'actor_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Актеры на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'actor')],
            context={'res_model': _name, 'tmp_res_model': 'actor'}),
        'agreed_actor_file': fields.char('Утвержденные актеры', size=250),

        'music': fields.boolean(
            'Музыкальное решение',
            readonly=True,
            states={
                'work': [('readonly', False)]
            }),
        'music_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Музыкальное решение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'music')],
            context={'res_model': _name, 'tmp_res_model': 'music'}),

        'another_param_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Другие параметры на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'another_params')],
            context={'res_model': _name, 'tmp_res_model': 'another_params'}),
        'selected_another_params_file': fields.text('Утвержденные параметры'),

        'application_date_ids': fields.one2many('process.video.applications', 'process_id', 'Приложения к договору'),

        'param_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Параметры создаваемого продукта',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'params')],
            context={'res_model': _name, 'tmp_res_model': 'params'}),
        'selected_param_file': fields.text('Выбранные параметры'),
        'comment_rw': fields.text("Комментарий по доработке"),

        'test_url': fields.char("Тестовая ссылка на готовый продукт", size=250),
        'ready_url': fields.char("Ссылка на готовый продукт", size=250),
        'comment_work': fields.text("Комментарий по выполненой работе"),
        'real_url': fields.char("Ссылка для передачи продукта", size=250),
        'anim_url': fields.char("Ссылка на утвержденное анимационное решение", size=250),
        'work_state': fields.selection(
            (
                ('graphic', 'Графика'),
                ('speaker', 'Дикторы'),
                ('actor', 'Актеры'),
                ('music', 'Музыкальное решение'),
            ),
            'Статус работы',
            readonly=True,
            states={
                'work': [('readonly', False)]
            }),

        'sla_ids': fields.one2many(
            'process.sla',
            'process_id',
            'SLA',
            domain=[('process_model', '=', _name)],
            context={'type': 'video', 'process_model': _name}),

        'check_a': fields.function(
            _check_access,
            method=True,
            string='Проверка на автора',
            type='boolean',
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string='Проверка на руководителя',
            type='boolean',
            invisible=True
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на специалиста',
            type='boolean',
            invisible=True
        ),
    }

    _defaults = {
        'state': 'coordination',
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        error = ''
        for key in ['report_ids', 'message_ids']:
            for item in values.get(key, []):
                if item[0] == 0:
                    item[2]['process_model'] = self._name

        for record in self.read(cr, uid, ids, []):
            next_state = values.get('state', False)
            state = record['state']

            if next_state and next_state != state:
                if next_state == 'filling_TK' and state == 'coordination' and (
                        not values.get('product_type', False) and not record['product_type']):
                    error += 'Необходимо выбрать вид создаваемого продукта'

                if next_state == 'filling_TK' and state == 'matching_TK' and (
                        not values.get('comment_rework', False) and not record['comment_rework']):
                    error += 'Необходимо заполнить комментарий по доработке ТЗ'

                if next_state == 'selection' and state == 'development' and (
                        not values.get('variant_ids', False) and not record['variant_ids']):
                    error += 'Необходимо заполнить варианты идей'

                if state == 'selection':
                    if next_state == 'development' and (
                            not values.get('comment_rework_idea', False) and not record['comment_rework_idea']):
                        error += 'Необходимо заполнить комментарий по доработке идей'

                    if next_state == 'drawing_up' and (not values.get('idea_file', False) and not record['idea_file']):
                        error += 'Необходимо заполнить выбранную идею'

                if next_state == 'matching_script' and state == 'drawing_up' and (
                        not values.get('scenario_ids', False) and not record['scenario_ids']):
                    error += 'Необходимо заполнить варианты сценариев'

                if next_state == 'drawing_up' and state == 'matching_script' and (
                        not values.get('comment_rework_scenario', False) and not record['comment_rework_scenario']):
                    error += 'Необходимо заполнить комментарий по доработке сценария'

                if next_state == 'signing_application' and state == 'matching_script' and (
                        not values.get('agreed_scenario_file', False) and not record['agreed_scenario_file']):
                    error += 'Необходимо заполнить утвержденный сценарий'

                if next_state == 'approval' and state == 'preparation' and (
                        not values.get('comment_rw', False) and not record['comment_rw']):
                    error += 'Необходимо заполнить комментарий по доработке'

                if state == 'approval':
                    if next_state == 'preparation' and (
                            not values.get('param_ids', False) and not record['param_ids']):
                        error += 'Необходимо заполнить параметры создаваемого продукта'
                    if next_state == 'work' and (
                            not values.get('selected_param_file', False) and not record['selected_param_file']):
                        error += 'Необходимо заполнить выбранные параметры'

                if state == 'work' and next_state == 'assertion' and (not values.get('test_url') and not record['test_url']):
                    error += 'Необходимо заполнить тестовую ссылку на готовый продукт'

                if state == 'assertion' and next_state == 'transmission' and (not values.get('test_url') and not record['test_url']):
                    error += 'Необходимо заполнить ссылку на готовый продукт'

                if error:
                    raise osv.except_osv("Video", error)

                values.update({
                    'history_ids': [
                        (0, 0, {
                            'state': self.get_state(STATES, next_state)[1],
                            'process_model': self._name
                        })
                    ]})
        return super(ProcessVideo, self).write(cr, uid, ids, values, context)
ProcessVideo()


class ProcessVideoApplications(Model):
    _name = 'process.video.applications'
    _inherit = 'process.base.staff'
    _description = u'VIDEO - Приложения к договору'
    _log_create = True

    _columns = {
        'name': fields.datetime('Дата подписания'),
        'attachment_id': fields.many2one(
            'ir.attachment',
            'Прикрепленный файл',
            domain=[('res_model', '=', _name)],
            context={'res_mode': _name}),
    }

    _defaults = {
        'process_model': 'process.video',
    }
ProcessVideoApplications()