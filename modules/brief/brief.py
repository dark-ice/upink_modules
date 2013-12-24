# -*- encoding: utf-8 -*-
import logging
from openerp.osv.osv import except_osv
import pytz

from datetime import datetime, timedelta, date
from openerp.osv.orm import Model
from openerp.osv import fields

from notify import notify
import time


_logger = logging.getLogger(__name__)


MODULE_IDS = (
    'brief.main',
    'brief.part.one',
    'brief.part.two',
    'brief.part.three',
    'brief.part.four',
    'brief.part.five',
    'brief.part.six'
)


class BriefContextAdv(Model):
    _name = "brief.context_adv"
    _description = u"Справочник систем размещения контекстной рекламы"
    _order = 'name'
    _columns = {
        'name': fields.char(u'Наименование системы контекстной рекламы', size=256),
    }
BriefContextAdv()


class BriefOutServices(Model):
    _name = "brief.out_services"
    _description = u"Справочник исходящих услуг call-центра UpSale"
    _order = 'name'
    _columns = {
        'name': fields.char(u'Наименование исходящих услуг', size=256),
    }
BriefOutServices()


class BriefInServices(Model):
    _name = "brief.in_services"
    _description = u"Справочник входящих услуг call-центра UpSale"
    _order = 'name'
    _columns = {
        'name': fields.char(u'Наименование входящих услуг', size=256),
    }
BriefInServices()


class BriefLang(Model):
    _name = "brief.lang"
    _description = u"Справочник иностранных языков"
    _order = 'name'
    _columns = {
        'name': fields.char(u'Иностранный язык', size=256),
    }
BriefLang()


class BriefTelType(Model):
    _name = "brief.tel_type"
    _description = u"Справочник типов номеров"
    _order = "name"
    _columns = {
        'name': fields.char(u'Тип номера партнера', size=256),
    }
BriefTelType()


class BriefDatabase(Model):
    _name = "brief.database"
    _description = u"Справочник баз данных"
    _order = "name"
    _columns = {
        'name': fields.char(u'Тип базы данных', size=256),
    }
BriefDatabase()


class BriefTargetAge(Model):
    _name = "brief.target_age"
    _description = u"Справочник групп возраста"
    _order = "name"
    _columns = {
        'name': fields.char(u'Возрастная группа', size=256),
    }
BriefTargetAge()


class BriefTargetIncome(Model):
    _name = "brief.target_income"
    _description = u"Справочник групп по уровню дохода"
    _order = "name"
    _columns = {
        'name': fields.char(u'Уровень доходов', size=256),
    }
BriefTargetIncome()


class BriefTargetRegion(Model):
    _name = "brief.target_region"
    _description = u"Справочник возможных целевых регионов"
    _order = "name"
    _columns = {
        'name': fields.char(u'Целевой регион', size=256),
    }
BriefTargetRegion()


class BriefServiceStage(Model):
    _name = "brief.services.stage"
    _description = u"Услуги"

    _columns = {
        'name': fields.char(u'Название', size=255, select=True),
        'usergroup': fields.many2one(
            'res.groups',
            u'Группа специалистов операционного направления',
            select=True),
        'leader_group_id': fields.many2one(
            'res.groups',
            u'Группа руководителя операционного направления'
        ),
        'check_leader': fields.boolean(u"Трубуется проверка руководителя операционного направления"),
        'direction': fields.char(u"Направление", size=255),
        'in_account': fields.boolean(u"Можно ли выставлять счет на услугу"),
        'service_type': fields.selection(
            (
                ('project', 'Проектная'),
                ('process', 'Процессная'),
            ), 'Тип'
        ),
        'template_id': fields.many2one('ir.attachment', 'Файл шаблона договора'),
    }

    _defaults = {
        'in_account': True,
        'service_type': 'process'
    }
BriefServiceStage()


class BriefRelServicesFields(Model):
    _name = "brief.rel_services_fields"
    _description = u"Связь между услугами и полями"
    _rec_name = 'service_id'

    def _check_unique_service(self, cr, uid, ids):
        """
            Проверка уникальности услуги.
            На одну услу не может быть назначено несколько вариантов полей.
        """
        fields = self.browse(cr, uid, ids[0])
        service_ids = self.search(cr, uid, [('service_id', '=', fields.service_id.id)], context=None)
        if len(service_ids) > 1:
            return False
        return True

    _columns = {
        'service_id': fields.many2one('brief.services.stage', 'Услуги компании', select=True),
        'fields_ids': fields.many2many(
            'ir.model.fields',
            'brief_service_fields_relation',
            'brief_id',
            'field_id',
            u'Доступные поля',
            domain=['&', ('model_id', 'in', MODULE_IDS), ('field_description', '!=', '')]),
        'fields_req': fields.many2many(
            'ir.model.fields',
            'brief_required_fields_rel',
            'b_id',
            'field_id',
            u'Обязательные поля',
            domain="[('id','in',fields_ids[0][2])]"),
    }

    _constraints = [
        (_check_unique_service,
         'По данной услуге уже назначен список полей, измените их.',
         ['service_id']),
    ]
BriefRelServicesFields()


class BriefPartOne(Model):
    _name = 'brief.part.one'
    _description = u"Бриф. Первая часть таблицы"
   
    _columns = {
        'algorithm': fields.selection(
            [
                ('one', 'Вариант 1'),
                ('two', 'Вариант 2'),
            ],
            u'Алгоритм предоставления услуги АПТ',
            help='Необходимое условие для просчета, которое может повысить конверсию продаж. Вариант 1. Один прозвон. Первый прозвон – оправка информации заинтересованным – передача контактов менеджерам Партнера. \тВариант 2. Два прозвона. Первый прозвон -отправление информации заинтересованным – второй прозвон – подтверждение интереса по информации – передача менеджерам партнера.'),
        'social_net': fields.char(
            u'В каких социальных сетях вы бы хотели запустить рекламу?',
            size=256,
            help=''),
        'work_dir': fields.char(
            u'В каком направлении должна вестись работа?',
            size=256,
            help=''),
        'name': fields.char(
            u'Имя и фамилия заказчика',
            size=64,
            help=''),
        'job_position': fields.char(
            u'Должность заказчика',
            size=64,
            help=''),
        'phone': fields.char(
            u'Контактный телефон заказчик',
            size=64,
            help=''),
        'email': fields.char(
            u'Эл.почта заказчика',
            size=128,
            help=''),
        'comp_adv': fields.char(
            u'Ваши конкурентные преимущества:',
            size=256,
            help=''),
        'media_expec': fields.char(
            u'Ваши ожидания от провижения в социальных медиа?',
            size=256,
            help=''),
        'web_sites': fields.char(
            u"Веб-сайты компании",
            size=256,
            help=u"Если несколько, то укажите 2-3"),
        'soc_services': fields.char(
            u'Виды услуг и/или инструменты социальных медиа, которые, по вашему мнению, являются приоритетными',
            size=256,
            help=''),
        'call_can': fields.char(
            u'Время работы операторов контакт-центра UpSale(пн-пт, выходные)',
            size=256,
            help=''),
    }
BriefPartOne()


class BriefPartTwo(Model):
    _name = "brief.part.two"
    _description = u"Бриф. Вторая часть таблицы"
    _rec_name = "add_mat"
    _columns = {
        'receive_file': fields.char(
            u'Готовы ли вы предоставить баннеры, фотоснимики товаров/услуг?',
            size=256,
            help=''
        ),
        'give_presents': fields.char(
            u'Готовы ли предоставить подарки, скидки пользователям?',
            size=256,
            help=''),
        'work_schedule': fields.char(
            u'График работы вашего офиса',
            size=256,
            help=''),
        'startup_date': fields.char(
            u'Дата выхода Компании/Бренда на рынок',
            size=256,
            help=''),
        'add_mat': fields.char(
            u'Есть ли готовые материалы для подготовки КЦ (речевой модуль для операторов, обучающие материалы, инструкции)?',
            size=256,
            help=''),
        'partner_mat': fields.char(
            u'Есть ли дополнительные материалы для работы с клиентами Партнера?',
            size=256,
            help=''),
        'user_wanted': fields.char(
            u'Желаемое количество посетителей (с примерами сайтов с такой посещаемостью)',
            size=256,
            help=''),
        'targ_keywords': fields.char(
            u'Желаемые ключевые запросы',
            size=256,
            help=''),
        'context_adv': fields.many2many(
            'brief.context_adv',
            'brief_context_adv_rel',
            'brief_id',
            'context_id',
            u'Желаемые системы размещения контекстной рекламы',
            help=''),
        'out_services': fields.many2many(
            'brief.out_services',
            'brief_out_services_rel',
            'brief_id',
            'out_services_id',
            u'Исходящие услуги контакт-центра UpSale',
            help=''),
        'in_services': fields.many2many(
            'brief.in_services',
            'brief_in_services_rel',
            'brief_id',
            'in_services_id',
            u'Входящие услуги контакт-центра UpSale',
            help=''),
        'lang': fields.many2many(
            'brief.lang',
            'brief_lang_rel',
            'brief_id',
            'lang_id', u'Знание иностранных языков',
            help='')
    }
BriefPartTwo()


class BriefPartThree(Model):
    _name = "brief.part.three"
    _description = u"Бриф. Третья часть таблицы"
    _rec_name = "another_lang"
    _columns = {
        'another_lang': fields.char(
            u'Другой иностранный язык',
            size=256,
            help=''),
        'int_mark': fields.char(
            u'Используемый инструменты интернет маркетинга',
            size=256,
            help=''),
        'duration': fields.char(
            u'Какие сроки с указанными объемом базы данных вам необходимы?',
            size=256,
            help=''),
        'leads_num': fields.char(
            u'Какое количество контактов Вы хотите чтобы было обработано КЦ (шт.)?',
            size=256,
            help=''),
        'calls_num': fields.char(
            u'Какое количество телефонных звонков, по Вашим расчетам, будет поступать в рабочее время? Указать в формате "в час/в день/в месяц"',
            size=256,
            help=''),
        'obj_keys': fields.char(
            u'Критерии измерения достижения целей',
            size=256,
            help=''),
        'ad_comp_dur': fields.char(
            u'Минимальный срок рекламной кампании (от 3мес. и более)',
            size=256,
            help=''),
        'cms_name': fields.char(
            u'Название CMS',
            size=256,
            help=''),
        'act_prior': fields.char(
            u'Наиболее приоритетные направления деятельности компании',
            size=256,
            help=''),
        'webmasters': fields.char(
            u'Наличие доступов к Google webmasters (reklama@upsale.ru) или Yandex webmasters (reklama.upsale)',
            size=256,
            help=''),
        'analytics': fields.char(
            u'Наличие доступов к Google. Analytics (reklama@upsale.ru) или Yandex.Metrika (reklama.upsale)',
            size=256,
            help=''),
        'ivr': fields.selection(
            [
                ('yes', 'Да'),
                ('no', 'Нет')
            ],
            u'Необходима ли запись и подключение IVR, автоответчика',
            select=True,
            help=''),
    }
BriefPartThree()


class BriefPartFour(Model):
    _name = "brief.part.four"
    _description = u"Бриф. Четвертая часть таблицы"
    _rec_name = "exp_visit"
    _columns = {
        'tel_type': fields.many2one(
            'brief.tel_type',
            u'Необходимо указать информацию на какой номер будут поступать звонки: на номер партнера или на тот, который нужно арендовать.',
            select=True,
            help=''),
        'an_tel_type': fields.char(
            u'Другой вариант номера',
            size=256,
            help=''),
        'exp_visit': fields.char(
            u'Ожидаемое действие от посетителя сайта',
            size=256,
            help=''),
        'adv_types': fields.char(
            u'Опишите виды рекламы, которые Вы используете сейчас/планируете использовать в ближайшее время',
            size=256,
            help=''),
        'smm_optimiz': fields.char(
            u'Оптимизирован ли Ваш сайт под работу с социальными медиа?',
            size=256,
            help=''),
        'sales_type': fields.selection(
            [
                ('opt', 'Оптовые'),
                ('rozn', 'Розничные'),
                ('opt_rozn', 'Оптовые и Розничные'),
                ('other', 'Другое')
            ],
            u'Тип продажи',
            select=True,
            help=''),
        'main_compete': fields.char(
            u'Основные конкуренты',
            size=256,
            help=''),
        'report_req': fields.char(
            u'Особые пожелания к отчетности',
            size=256,
            help=''),
        'info_req': fields.char(
            u'Перечень информации, обязательной для упоминания(уточните)',
            size=256,
            help=''),
        'budget': fields.integer(
            u'Планируемый бюджет руб./мес.',
            help=''),
        'question_par': fields.char(
            u'По каким вопросам наш сотрудник обязан во всех случаях согласовывать ответы на комментарии или вопросы других пользователей? (наш сотрудник будет отвечать только в рамках предоставленной заказчиком информации)',
            size=256,
            help=''),
    }
BriefPartFour()


class BriefPartFive(Model):
    _name = "brief.part.five"
    _description = u"Бриф. Пятая часть таблицы"
    _rec_name = "database_type"
    _columns = {
        'database_type': fields.many2one(
            'brief.database',
            u'По какой базе будет проводиться работа КЦ?',
            help=''),
        'target_sex': fields.selection(
            [
                ('men', 'Мужчины'),
                ('women', 'Женщины'),
                ('nomatter', 'Не имеет значения')
            ],
            u'Портрет целевой аудитории (пол):',
            help=''),
        'target_age': fields.many2one(
            'brief.target_age',
            u'Портрет целевой аудитории (возрастная группа):',
            help=''),
        'target_income': fields.many2one(
            'brief.target_income',
            u'Портрет целевой аудитории (уровень доходов):',
            help=''),
        'target_activ': fields.char(
            u'Портрет целевой аудитории (род деятельности):',
            size=256,
            help=''),
        'target_living': fields.char(
            u'Портрет целевой аудитории (место проживания):',
            size=256,
            help=''),
        'target_inter': fields.char(
            u'Портрет целевой аудитории (интересы):',
            size=256,
            help=''),
        'social_pres': fields.char(
            u'Представлена ли на данный момент Ваша компания в социальных сетях, форумах и т.д.? Если да, то каким образом? (укажите URL-адреса всех Ваших сообществ)',
            size=256,
            help=''),
        'talk_time': fields.char(
            u'Примерная длительность времени разговора (контакта) оператора с Клиентом (мин.)',
            size=256,
            help=''),
        'site_age': fields.char(
            u'Сколько лет сайту (не домену, а именно сайту)',
            size=256,
            help=''),
        'operators_tobe': fields.char(
            u'Сколько операторов нужно Вам для работы?',
            size=256,
            help=''),
    }
BriefPartFive()


class BriefPartSix(Model):
    _name = "brief.part.six"
    _description = u"Бриф. Шестая часть таблицы"
    _rec_name = "operators_asis"
    _columns = {
        'operators_asis': fields.char(
            u'Сколько операторов работает у Вас сейчас?',
            size=256,
            help=''),
        'adv_duration': fields.char(
            u'Сроки проведения рекламной кампании',
            size=256,
            help=''),
        'company_theme': fields.char(
            u'Тематика компании/бренда',
            size=256,
            help=''),
        'forums_tobe': fields.char(
            u'Форумы, на которых обязательно должны быть размещены посты (или информация)',
            size=256,
            help=''),
        'target_region': fields.many2one(
            'brief.target_region',
            u'Целевой регион',
            help=''),
        'another_region': fields.char(
            u'Другой целевой регион',
            size=256,
            help=''),
        'work_object': fields.char(
            u'Цель работы? Чего Вы желаете добиться, используя скрытый маркетинг (чем подробнее, тем лучше)',
            size=256,
            help=''),
        'soc_reasons': fields.char(
            u'Что Вас подтолкнуло прийти в соцсети?',
            size=256,
            help=''),
        'adv_object': fields.char(
            u'Что станет рекламируемым объектом? - сайт компании (имиджевая реклама) - определенные товары (укажите, пожалуйста, ссылки на них) представительство (группа, сообщество) в социальных сетях',
            size=256,
            help=''),
        'another_plase_reklam': fields.char(
            u'Где размещали рекламу в Интернете?',
            size=256,
            help=''),
        'type_of_promotion': fields.selection(
            [
                ('no choice', 'Не выбрано'),
                ('by words', 'По словам'),
                ('by traffic', 'По трафику')
            ],
            u'Тип продвижения',
            help=''
        ),
        'tech_spec': fields.char(
            u'Есть ли технический специалист, который будет вносить необходимые изменения на сайт',
            size=256,
            help=''),
        'other_direction_reclam': fields.char(
            u'Укажите другие направления рекламы, которые Вы использовали ранее',
            size=256,
            help=''),
        'count_see': fields.integer('Количество просмотров')
    }
BriefPartSix()


class BriefCbOne(Model):
    _name = "brief.checkboxes.one"
    _description = u"Бриф. Вспомогательная часть 1"
    _rec_name = "algorithm_cb"
    _columns = {
        'algorithm_cb': fields.boolean('1'),
        'social_net_cb': fields.boolean('2'),
        'work_dir_cb': fields.boolean('3'),
        'name_cb': fields.boolean('4'),
        'job_position_cb': fields.boolean('5'),
        'phone_cb': fields.boolean('6'),
        'email_cb': fields.boolean('7'),
        'comp_adv_cb': fields.boolean('8'),
        'media_expec_cb': fields.boolean('9'),
        'web_sites_cb': fields.boolean('10'),
        'soc_services_cb': fields.boolean('11'),
        'call_can_cb': fields.boolean('12'),
        'receive_file_cb': fields.boolean('13'),
        'give_presents_cb': fields.boolean('14'),
        'work_schedule_cb': fields.boolean('15'),
        'startup_date_cb': fields.boolean('16'),
        'add_mat_cb': fields.boolean('17'),
        'partner_mat_cb': fields.boolean('18'),
        'user_wanted_cb': fields.boolean('19'),
        'targ_keywords_cb': fields.boolean('20'),
        'context_adv_cb': fields.boolean('21'),
        'out_services_cb': fields.boolean('22'),
        'in_services_cb': fields.boolean('23'),
        'lang_cb': fields.boolean('24'),
    }
BriefCbOne()


class BriefCbTwo(Model):
    _name = "brief.checkboxes.two"
    _description = u"Бриф. Вспомогательная часть 2"
    _rec_name = "int_mark_cb"
    _columns = {
        'int_mark_cb': fields.boolean('25'),
        'duration_cb': fields.boolean('26'),
        'leads_num_cb': fields.boolean('27'),
        'calls_num_cb': fields.boolean('28'),
        'obj_keys_cb': fields.boolean('29'),
        'ad_comp_dur_cb': fields.boolean('30'),
        'cms_name_cb': fields.boolean('31'),
        'act_prior_cb': fields.boolean('32'),
        'webmasters_cb': fields.boolean('33'),
        'analytics_cb': fields.boolean('34'),
        'ivr_cb': fields.boolean('35'),
        'tel_type_cb': fields.boolean('36'),
        'exp_visit_cb': fields.boolean('37'),
        'adv_types_cb': fields.boolean('38'),
        'smm_optimiz_cb': fields.boolean('39'),
        'sales_type_cb': fields.boolean('40'),
        'main_compete_cb': fields.boolean('41'),
        'report_req_cb': fields.boolean('42'),
        'info_req_cb': fields.boolean('43'),
        'budget_cb': fields.boolean('44'),
        'question_par_cb': fields.boolean('45'),
        'database_type_cb': fields.boolean('46'),
    }
BriefCbTwo()


class BriefCbThree(Model):
    _name = "brief.checkboxes.three"
    _description = u"Бриф. Вспомогательная часть 3"
    _rec_name = "target_sex_cb"
    _columns = {
        'target_sex_cb': fields.boolean('47'),
        'target_age_cb': fields.boolean('48'),
        'target_income_cb': fields.boolean('49'),
        'target_activ_cb': fields.boolean('50'),
        'target_living_cb': fields.boolean('51'),
        'target_inter_cb': fields.boolean('52'),
        'social_pres_cb': fields.boolean('53'),
        'talk_time_cb': fields.boolean('54'),
        'site_age_cb': fields.boolean('55'),
        'operators_tobe_cb': fields.boolean('56'),
        'database_type_cb': fields.boolean('57'),
        'operators_asis_cb': fields.boolean('68'),
        'adv_duration_cb': fields.boolean('69'),
        'company_theme_cb': fields.boolean('70'),
        'forums_tobe_cb': fields.boolean('71'),
        'target_region_cb': fields.boolean('72'),
        'work_object_cb': fields.boolean('73'),
        'soc_reasons_cb': fields.boolean('74'),
        'adv_object_cb': fields.boolean('75'),
        #-- New fields
        'another_plase_reklam_cb': fields.boolean('76_new'),
        'type_of_promotion_cb': fields.boolean('77_new'),
        'tech_spec_cb': fields.boolean('79_new'),
        'other_direction_reclam_cb': fields.boolean('80_new'),

        'planned_budget_cb': fields.boolean('156_new'),
        'tender_cb': fields.boolean('157_new'),
        'tender_file_id_cb': fields.boolean('158_new'),
        'planned_works_cb': fields.boolean('159_new'),
        'solvency_cb': fields.boolean('160_new'),
        'history_and_cb': fields.boolean('161_new'),
        'develop_info_cb': fields.boolean('162_new'),
        'another_content_cb': fields.boolean('163_new'),
        'brief_file_id_cb': fields.boolean('164_new'),
        'text_content_cb': fields.boolean('165_new'),
        'need_text_cb': fields.boolean('166_new'),
        'vol_text_cb': fields.boolean('167_new'),
        'sources_seo_cb': fields.boolean('168_new'),
        'newsmaker_cb': fields.boolean('169_new'),
        'in_silence_cb': fields.boolean('170_new'),
        'purpose_cb': fields.boolean('171_new'),
        'what_sell_cb': fields.boolean('172_new'),
        'where_cb': fields.boolean('173_new'),
        'sources_info_cb': fields.boolean('174_new'),
        'distinguishes_cb': fields.boolean('175_new'),
        'problem_resolve_cb': fields.boolean('176_new'),
        'hidden_desires_cb': fields.boolean('177_new'),
        'benefit_cb': fields.boolean('178_new'),
        'why_you_cb': fields.boolean('179_new'),
        'marketing_cb': fields.boolean('180_new'),
        'transfer_cb': fields.boolean('181_new'),
        'access_ids_cb': fields.boolean('182_new'),
        'count_see_cb': fields.boolean('183'),
    }
BriefCbThree()


class BriefCbrOne(Model):
    _name = "brief.checkboxes.four"
    _description = u"Бриф. Вспомогательная часть 4"
    _rec_name = "algorithm_cbr"
    _columns = {
        'algorithm_cbr': fields.boolean('76'),
        'social_net_cbr': fields.boolean('77'),
        'work_dir_cbr': fields.boolean('78'),
        'name_cbr': fields.boolean('79'),
        'job_position_cbr': fields.boolean('80'),
        'phone_cbr': fields.boolean('81'),
        'email_cbr': fields.boolean('82'),
        'comp_adv_cbr': fields.boolean('83'),
        'media_expec_cbr': fields.boolean('84'),
        'web_sites_cbr': fields.boolean('85'),
        'soc_services_cbr': fields.boolean('86'),
        'call_can_cbr': fields.boolean('87'),
        'receive_file_cbr': fields.boolean('88'),
        'give_presents_cbr': fields.boolean('89'),
        'work_schedule_cbr': fields.boolean('90'),
        'startup_date_cbr': fields.boolean('91'),
        'add_mat_cbr': fields.boolean('92'),
        'partner_mat_cbr': fields.boolean('93'),
        'user_wanted_cbr': fields.boolean('94'),
        'targ_keywords_cbr': fields.boolean('95'),
        'context_adv_cbr': fields.boolean('96'),
        'out_services_cbr': fields.boolean('97'),
        'in_services_cbr': fields.boolean('98'),
        'lang_cbr': fields.boolean('99'),
    }
BriefCbrOne()


class BriefCbrTwo(Model):
    _name = "brief.checkboxes.five"
    _description = u"Бриф. Вспомогательная часть 5"
    _rec_name = "int_mark_cbr"
    _columns = {
        'int_mark_cbr': fields.boolean('100'),
        'duration_cbr': fields.boolean('101'),
        'leads_num_cbr': fields.boolean('102'),
        'calls_num_cbr': fields.boolean('103'),
        'obj_keys_cbr': fields.boolean('104'),
        'ad_comp_dur_cbr': fields.boolean('105'),
        'cms_name_cbr': fields.boolean('106'),
        'act_prior_cbr': fields.boolean('107'),
        'webmasters_cbr': fields.boolean('108'),
        'analytics_cbr': fields.boolean('109'),
        'ivr_cbr': fields.boolean('110'),
        'tel_type_cbr': fields.boolean('111'),
        'exp_visit_cbr': fields.boolean('112'),
        'adv_types_cbr': fields.boolean('113'),
        'smm_optimiz_cbr': fields.boolean('114'),
        'sales_type_cbr': fields.boolean('115'),
        'main_compete_cbr': fields.boolean('116'),
        'report_req_cbr': fields.boolean('117'),
        'info_req_cbr': fields.boolean('118'),
        'budget_cbr': fields.boolean('119'),
        'question_par_cbr': fields.boolean('120'),
        'database_type_cbr': fields.boolean('121'),
    }
BriefCbrTwo()


class BriefCbrThree(Model):
    _name = "brief.checkboxes.six"
    _description = u"Бриф. Вспомогательная часть 6"
    _rec_name = "target_sex_cbr"
    _columns = {
        'target_sex_cbr': fields.boolean('122'),
        'target_age_cbr': fields.boolean('123'),
        'target_income_cbr': fields.boolean('124'),
        'target_activ_cbr': fields.boolean('125'),
        'target_living_cbr': fields.boolean('126'),
        'target_inter_cbr': fields.boolean('127'),
        'social_pres_cbr': fields.boolean('128'),
        'talk_time_cbr': fields.boolean('129'),
        'site_age_cbr': fields.boolean('130'),
        'operators_tobe_cbr': fields.boolean('131'),
        'database_type_cbr': fields.boolean('132'),
        'operators_asis_cbr': fields.boolean('143'),
        'adv_duration_cbr': fields.boolean('144'),
        'company_theme_cbr': fields.boolean('145'),
        'forums_tobe_cbr': fields.boolean('146'),
        'target_region_cbr': fields.boolean('147'),
        'work_object_cbr': fields.boolean('148'),
        'soc_reasons_cbr': fields.boolean('149'),
        'adv_object_cbr': fields.boolean('150'),
        #-- New fields
        'another_plase_reklam_cbr': fields.boolean('151'),
        'type_of_promotion_cbr': fields.boolean('152'),
        'tech_spec_cbr': fields.boolean('154'),
        'other_direction_reclam_cbr': fields.boolean('155'),

        'planned_budget_cbr': fields.boolean('156'),
        'tender_cbr': fields.boolean('157'),
        'tender_file_id_cbr': fields.boolean('158'),
        'planned_works_cbr': fields.boolean('159'),
        'solvency_cbr': fields.boolean('160'),
        'history_and_cbr': fields.boolean('161'),
        'develop_info_cbr': fields.boolean('162'),
        'another_content_cbr': fields.boolean('163'),
        'brief_file_id_cbr': fields.boolean('164'),
        'text_content_cbr': fields.boolean('165'),
        'need_text_cbr': fields.boolean('166'),
        'vol_text_cbr': fields.boolean('167'),
        'sources_seo_cbr': fields.boolean('168'),
        'newsmaker_cbr': fields.boolean('169'),
        'in_silence_cbr': fields.boolean('170'),
        'purpose_cbr': fields.boolean('171'),
        'what_sell_cbr': fields.boolean('172'),
        'where_cbr': fields.boolean('173'),
        'sources_info_cbr': fields.boolean('174'),
        'distinguishes_cbr': fields.boolean('175'),
        'problem_resolve_cbr': fields.boolean('176'),
        'hidden_desires_cbr': fields.boolean('177'),
        'benefit_cbr': fields.boolean('178'),
        'why_you_cbr': fields.boolean('179'),
        'marketing_cbr': fields.boolean('180'),
        'transfer_cbr': fields.boolean('181'),
        'access_ids_cbr': fields.boolean('182'),
        'count_see_cbr': fields.boolean('183'),
    }
BriefCbrThree()


class BriefLoyalty(Model):
    _name = 'brief.loyality'
    _description = u"Программы лояльности"
    _columns = {
        'name': fields.char(u"Программа лояльности", size=256)
    }
BriefLoyalty()


class ResPartner(Model):
    _inherit = "res.partner"

    _columns = {
        'brief_ids': fields.one2many(
            'brief.main',
            'partner_id',
            u'Брифы на просчет'
        ),
    }

    def create_brief(self, cr, uid, ids, context=None):
        """
            Открывает окно с брифом и переданными данными
        """
        data = False
        if ids:
            action_pool = self.pool.get('ir.actions.act_window')
            action_id = action_pool.search(cr, uid, [('name', '=', 'Создать бриф из кандидата')], context=context)
            partner_obj = self.browse(cr, uid, ids[0], context=context)
            if action_id:
                data = action_pool.read(cr, uid, action_id[0], context=context)

                if partner_obj.address:
                    name = partner_obj.address[0].name
                    email = partner_obj.address[0].email
                    job_position = partner_obj.address[0].function
                else:
                    name = None
                    email = None
                    job_position = None

                data.update({
                    'nodestroy': True,
                    'context': {
                        'partner_id': ids[0],
                        'partner_name': partner_obj.name,
                        'name': name,
                        'email': email,
                        'job_position': job_position,
                        'from': 'lp'
                    }
                })

        return data
ResPartner()


class Brief(Model):
    _name = 'brief.main'
    _description = u"Бриф"
    _rec_name = 'partner_id'

    _inherits = {
        'brief.part.one': 'brief_part_one_id',
        'brief.part.two': 'brief_part_two_id',
        'brief.part.three': 'brief_part_three_id',
        'brief.part.four': 'brief_part_four_id',
        'brief.part.five': 'brief_part_five_id',
        'brief.part.six': 'brief_part_six_id',
        'brief.checkboxes.one': 'brief_cb_one_id',
        'brief.checkboxes.two': 'brief_cb_two_id',
        'brief.checkboxes.three': 'brief_cb_three_id',
        'brief.checkboxes.four': 'brief_cbr_one_id',
        'brief.checkboxes.five': 'brief_cbr_two_id',
        'brief.checkboxes.six': 'brief_cbr_three_id',
    }

    _order = "id desc"

    _states = (
        ('draft', 'Черновик'),
        ('rework', 'Бриф на доработке'),
        ('accept', 'Бриф на согласовании'),
        ('inwork', 'Бриф принят'),
        ('media_accept_rev', 'Медиаплан на доработке (согласование)'),
        ('media_accept', 'Медиаплан на согласовании'),
        ('media_approval_r', 'Медиаплан на доработке (утверждение)'),
        ('media_approval', 'Медиаплан на утверждении'),
        ('partner_refusion', 'Партнер отказался'),
        ('media_approved', 'Медиаплан утвержден'),
        ('cancel', 'Заявка отменена'),
    )

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = []
        for r in self.read(cr, user, ids, ['specialist_id']):
            if r['specialist_id']:
                res.append((r['id'], "Бриф № {0} [{1}]".format(r['id'], r['specialist_id'][1].encode('utf-8'))))
            else:
                res.append((r['id'], "Бриф № {0}".format(r['id'],)))
        return res

    def action_add(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def onchange_cand_id(self, cr, uid, ids, cand_id, context=None):
        """
            Метод изменяет связанные с кандидатом характеристики при изменении
                кандидата
        """
        res = {}
        if cand_id:
            cand_obj = self.pool.get('res.partner').browse(cr, uid, cand_id, context=context)
            res = {
                'partner_name': cand_obj.name,
            }
        return {'value': res}

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split("\\")[-1]
        return {'value': res}

    def onchange_select(self, cr, uid, ids, services_ids, context=None):
        """
            Метод для отображения привязанных к услуге полей.
            Из объекта brief.rel_services_fields выбираются два набора полей
                @fields_ids - видимые поля
                @fields_req - обязательные поля
            Осуществляется проход по соотв. чекбоксам устанавливая значения в режив видимости
        """
        res = {}
        if services_ids:
            service_id = self.pool.get('brief.rel_services_fields').search(cr, uid, [
                ('service_id', '=', services_ids)
            ], context=context)
            if service_id:
                fields_object = self.pool.get('brief.rel_services_fields').read(cr, uid, service_id, [
                    'fields_ids',
                    'fields_req'
                ], context=context)
                visible_fields = self.pool.get('ir.model.fields').read(
                    cr,
                    uid,
                    fields_object[0]['fields_ids'],
                    ['name'],
                    context=context
                )
                for f_id in visible_fields:
                    checkbox_name = f_id['name'] + '_cb'
                    res[checkbox_name] = True
                required_fields = self.pool.get('ir.model.fields').read(
                    cr,
                    uid,
                    fields_object[0]['fields_req'],
                    ['name'],
                    context=context
                )
                for f_id in required_fields:
                    checkbox_name = f_id['name'] + '_cbr'
                    res[checkbox_name] = True
                data_service = self.pool.get('brief.services.stage').browse(cr, uid, services_ids)
                res['usergroup'] = data_service.usergroup.id
        return {'value': res}

    def _check_permissions(self, cr, uid, ids, field_name, arg, context=None):
        """
            Метод для динамического определения ролей в брифе.
        """
        res = {}
        data = self.browse(cr, uid, ids)
        for field in data:
            user_data = self.pool.get('res.users').browse(cr, uid, uid)
            manager_groups = 89
            specialist_groups = 142
            for group in user_data.groups_id:
                if not res:
                    if group.id == manager_groups:
                        res[field.id] = "Director"
                    elif group.id == specialist_groups:
                        res[field.id] = "Spec_Director"
                        #else:
                        #res[field.id] = "specialist"
            if not res:
                res[field.id] = "specialist"

                #print res[field.id]
        return res

    def timedelta_type(self, time_type, time):
        if time_type == 'hours':
            return timedelta(hours=time)
        elif time_type == 'minutes':
            return timedelta(minutes=time)
        elif time_type == 'days':
            return timedelta(days=time)

    def get_time(self, current_time, control_time=False):
        def get_day(current_time):
            day = current_time.isoweekday()
            if day == 7:
                return 1
            elif day == 6:
                return 2
            elif day == 5:
                return 3
            return False

        next_day = get_day(current_time)
        if current_time > current_time.replace(hour=18, minute=0):
            next_day = next_day or 1
            control_time = (current_time - current_time.replace(hour=18, minute=0)) if not control_time else control_time
            current_time = current_time.replace(hour=9, minute=0) + timedelta(days=next_day)
        if not control_time:
            return current_time
        current_time = current_time + control_time
        return self.get_time(current_time)

    def _check_budget(self, cr, uid, ids):
        """
            Проверка бюджета в случае, если поле обязательное
        """
        data = self.browse(cr, uid, ids[0])
        if data.budget == 0 and data.budget_cbr == True:
            return False
        return True

    def _check_mediaplan(self, cr, uid, ids):
        """
            Проверка наличия медиаплана на определенных этапах
        """
        data = self.read(cr, uid, ids[0], ['rep_file_id', 'state', 'file_name', 'media_plan'])
        if not data.get('rep_file_id') and not data.get('file_name') and not data.get('media_plan') and data['state'] not in ('draft', 'cancel', 'rework', 'accept', 'inwork'):
            return False
        return True

    def _check_accept(self, cr, uid, ids):
        """
            Проверка связи брифа с партнером или кандидатом
        """
        data = self.read(cr, uid, ids[0], ['state', 'partner_id'])
        if data['state'] == 'accept' and not data['partner_id']:
            return False
        return True

    def create(self, cr, user, vals, context=None):
        if vals.get('from'):
            del vals['from']
        if vals.get('partner_id'):
            self.pool.get('res.partner').write(cr, user, [vals['partner_id']], {'partner_base': 'hot'})
        return super(Brief, self).create(cr, user, vals, context)

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        if values.get('from', False):
            values['from'] = None

        if values.get('state', False):
            state = values.get('state', False)
            values.update({'history_ids': [
                (0, 0, {'us_id': uid, 'cr_date': time.strftime('%Y-%m-%d %H:%M:%S'), 'state': self.get_state(state)[1], 'state_id': state})]})
            for record in self.browse(cr, 1, ids):
                if state in ('media_approval', 'media_accept') and not (record.sum_mediaplan and values.get('sum_mediaplan')):
                    raise except_osv('Бриф на просчет', 'Необходимо ввести сумму медиалпана')
        return super(Brief, self).write(cr, uid, ids, values, context)

    def action_cancel(self, cr, uid, ids):
        return self.write(cr, uid, ids, {'state': 'cancel', 'deadline': False})

    def action_draft(self, cr, uid, ids):
        return self.write(cr, uid, ids, {'state': 'draft', 'deadline': False})

    def action_accept(self, cr, uid, ids):
        """
            При переходе на этап Бриф на согласовании:
                Происходит распределения брифа специалистам
                Алгоритм очереди реализован согласно ТЗ.
        """
        result = {}
        data = self.browse(cr, uid, ids[0])
        if data.state == 'draft':
            users = self.pool.get('res.users')
            admin = 1
            specialists = users.search(cr, admin, [('groups_id', 'in', data.services_ids.usergroup.id)], order='id')
            if not data.specialist_id and specialists:
                brief_ids = self.pool.get('brief.main').search(cr, admin,
                    [('specialist_id', 'in', specialists), ('state', '!=', 'draft'), ('round_datetime', '!=', False), ('specialist_id.groups_id', 'in', data.services_ids.usergroup.id)], order='round_datetime desc', limit=1)
                if brief_ids:
                    last_brief_data = self.pool.get('brief.main').browse(cr, admin, brief_ids[0])
                    user_position = specialists.index(last_brief_data.specialist_id.id)
                    if specialists[-1] == last_brief_data.specialist_id.id:
                        result['specialist'] = specialists[0]
                    else:
                        result['specialist'] = specialists[user_position + 1]
                else:
                    result['specialist'] = specialists[0]
                self.write(cr, uid, ids, {'specialist_id': result['specialist'], 'round_datetime': fields.datetime.now()})
        self.write(cr, uid, ids, {'state': 'accept', 'deadline': False})
        data = self.browse(cr, uid, ids[0])
        return [data.specialist_id.id]

    def action_rework(self, cr, uid, ids):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'rework', 'deadline': False})
        return [data.responsible_user.id]

    def action_inwork(self, cr, uid, ids):
        return self.write(cr, uid, ids, {'state': 'inwork', 'deadline': False})

    def action_media_accept(self, cr, uid, ids):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'media_accept', 'deadline': False})
        return [data.responsible_user.id]

    def action_media_accept_revision(self, cr, uid, ids):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'media_accept_rev', 'deadline': False})
        return [data.specialist_id.id]

    def action_media_approval(self, cr, uid, ids):
        return self.write(cr, uid, ids, {'state': 'media_approval', 'deadline': False})

    def action_media_approval_revision(self, cr, uid, ids):
        data = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'media_approval_r', 'deadline': False})
        return [data.specialist_id.id]

    def action_partner_refusion(self, cr, uid, ids):
        return self.write(cr, uid, ids, {'state': 'partner_refusion', 'deadline': False})

    def action_media_approved(self, cr, uid, ids):
        return self.write(cr, uid, ids, {'state': 'media_approved', 'deadline': False})

    def _get_accept_date(self, cr, uid, ids, field_name, field_value, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            date_str = datetime.strptime(record.create_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            result[record.id] = date_str.strftime('%Y-%m-%d %H:%M:%S')
        return result

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        @param cr: database cursor
        @param uid: userID
        @param ids: list brief id
        @param name: field name
        @param arg: args
        @param context: Context
        """
        res = {}
        for record in self.read(cr, uid, ids, ['responsible_user', 'specialist_id', 'leader_ids'], context):
            access = str()

            t_users = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', [142])], order='id')
             #  Менеджер продаж
            if record['responsible_user'][0] == uid or uid in t_users:
                access += 'm'

            #  Ответственный специалист
            if record['specialist_id'] and record['specialist_id'][0] == uid or uid in t_users:
                access += 'r'

            #  Руководитель направления
            if uid in record['leader_ids'] or uid in t_users:
                access += 'h'

            #  Видят все
            users = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', [48, 142])], order='id')
            if uid in users:
                access += 's'

            val = False
            letter = name[6]
            if letter in access:
                val = True

            res[record['id']] = val
        return res

    def check_delta(self, cr, brief_id, state='media_accept', delta=2):
        history_pool = self.pool.get('brief.history')
        history_accept_ids = history_pool.search(cr, 1, [('state_id', '=', state), ('brief_id', '=', brief_id)])
        if history_accept_ids:
            history_accept = history_pool.read(cr, 1, history_accept_ids, ['cr_date'])
            date_start = datetime.strptime(history_accept[0]['cr_date'].split('.')[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            tmd_date = date_start + timedelta(hours=delta)
            if tmd_date.hour > 17:
                tmd_date += timedelta(hours=17)

            wknum = date.weekday(tmd_date)
            if wknum in (5, 6):
                tmd_date += timedelta(days=7 - wknum)

            if tmd_date < datetime.now(pytz.utc):
                return True
        return False

    def _get_service_head(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context):
            service_head_group = record.services_ids.leader_group_id.id
            users = self.pool.get('res.users').search(
                cr,
                1,
                [
                    ('groups_id', 'in', service_head_group),
                    ('id', 'not in', [1, 5, 13, 18, 354])
                ],
                order='id')
            if record.state == 'media_accept':
                if self.check_delta(cr, record.id) and 472 not in users:
                    users.append(472)
            if users:
                res[record.id] = users
        return res

    def cron_check_head(self, cr, uid, context=None):
        brief_ids = self.search(cr, uid, [('state', '=', 'media_accept'), ('check_head', '=', False)])
        ids = [brief_id for brief_id in brief_ids if self.check_delta(cr, brief_id)]

        if ids:
            self.write(cr, uid, ids, {'check_head': True})

    def cron_check_long(self, cr, uid, context=None):
        brief_ids = self.search(cr, uid, [('state', 'in', ('accept', 'inwork', 'media_accept_rev', 'media_approval_r'))])

        ids = [brief['id'] for brief in self.read(cr, uid, brief_ids, ['state']) if self.check_delta(cr, brief['id'], brief['state'], delta=3)]

        if ids:
            self.write(cr, uid, ids, {'check_long': True})

    def cron_work_state(self, cr, uid, context=None):
        sql = """SELECT
                b.id
            FROM
                brief_main b
            WHERE
                b.state NOT IN ('draft', 'cancel') AND b.work_state != 'overdue' AND
            age(
                (SELECT COALESCE(max(cr_date), now() at time zone 'UTC')
                    FROM brief_history WHERE brief_id=b.id AND state_id = 'media_approval'),
                (SELECT min(cr_date)
                    FROM brief_history WHERE brief_id=b.id AND state_id = 'accept')) > interval '4 hours';"""
        cr.execute(sql)
        res_ids = set(brief_id[0] for brief_id in cr.fetchall())
        if res_ids:
            self.write(cr, uid, tuple(res_ids), {'work_state': 'overdue'})

    def get_state(self, state):
        return [item for item in self._states if item[0] == state][0]

    _columns = {
        'user_id': fields.many2one(
            'res.users',
            'Автор документа',
            readonly=True,
            help='Автор (менеджер продаж).'),
        'specialist_id': fields.many2one(
            'res.users',
            'Ответственный специалист',
            select=True,
            help='Сотрудник, ответственный за составление медиаплана.'),
        'brief_super': fields.many2one(
            'res.groups',
            'Админ',
            readonly=True,
            invisible=True,
            help=''),
        'partner_id': fields.many2one(
            'res.partner',
            'Партнер (основной сайт)',
            help='Парнер, по которому заполняется Бриф.'),
        'create_date': fields.date(
            'Дата заполнения',
            readonly=True,
            help='Дата заполнения Брифа'),
        'write_date': fields.datetime(
            'Дата изменения',
            readonly=True,
            help='Дата изменения Брифа.'),
        'partner_name': fields.char(
            'Название компании',
            size=64,
            help='Юридическое название компании'),
        'services_ids': fields.many2one(
            'brief.services.stage',
            'Наименование услуги',
            select=True,
            required=True,
            domain=[('usergroup', '!=', False)],
            help='Услуга по которой составляется Бриф.'),
        'direction': fields.function(
            lambda *a: dict((r_id, '') for r_id in a[3]),
            type="selection",
            method=True,
            string='Направление',
            help='',
            selection=[
                   ('PPC', 'PPC'),
                   ('VIDEO', 'VIDEO'),
                   ('SEO', 'SEO'),
                   ('SMM', 'SMM'),
                   ('CALL', 'CALL'),
                   ('SITE', 'SITE'),
                   ('MP', 'MP'),
            ],
        ),
        'state': fields.selection(
            _states,
            'Статус брифа',
            size=64,
            readonly=True,
            help='Текущий статус Брифа.'),
        'subject': fields.char(
            'Тематика',
            size=250,
            help='Категория, к которой принадлежит Кандидат(Партнер)'),
        'notes': fields.text(
            'Примечания менеджера',
            help='Примечания (комментарии) к Брифу.'),
        'comment_mp': fields.text(
            'Коментарии медиапланера',
            help='Поле для внесения комментария'),
        'comment_revision': fields.text(
            'Коментарии по доработке МП',
            help='Поле для внесения комментария'),
        'responsible_user': fields.many2one(
            'res.users',
            'Менеджер продаж',
            select=True,
            help='Менеджер продаж'),
        'permissions': fields.function(
            _check_permissions,
            type="char",
            obj="brief.main",
            method=True,
            string="Права доступа",
            help=''
        ),
        'usergroup': fields.many2one(
            'res.groups',
            'Группа',
            help=''),
        'rep_file_id': fields.one2many(
            'attach.files',
            'obj_id',
            'Медиаплан/коммерческое предложение',
            help='Поле для загрузки медиаплана. Заполняется медиапланером.'),
        'media_plan': fields.binary(
            'Медиаплан/коммерческое предложение',
            help=''),
        'file_name': fields.char(
            'Название медиплана',
            size=250,
            help=''),
        'deadline': fields.datetime(
            'Контроль сроков',
            readonly=True,
            help=''
        ),
        'round_datetime': fields.datetime(
            'Дата распределения',
            help=''),

        # История
        'history_ids': fields.one2many(
            'brief.history',
            'brief_id',
            'История',
            readonly="1",
            help='Таблица переходов текущей карточки, заполняется автоматически'),

        'accept_date': fields.function(
            _get_accept_date,
            type="datetime",
            store=True,
            method=True,
            string="Бриф на согласовании",
            help=''),

        'loyality_id': fields.many2one(
            'brief.loyality',
            'Участие в программах лояльности компании',
            help='Участие в программах лояльности компании'),
        'planned_budget': fields.char(
            "Планируемый бюджет",
            size=256,
            help=''),
        'tender': fields.text(
            'Тендер/Условия тендера',
            help=''),
        'planned_works': fields.text(
            'Планирование дальнейших работ',
            help="Планируют ли заказывать у нас внедрение изменений по результатам"
                 " аудита или будут внедрять силами своих специалистов"),
        'solvency': fields.text(
            'Платежеспособность',
            help=''
        ),
        'history_and': fields.text(
            'История и перспективы отношений',
            help=''),
        'develop_info': fields.text(
            'Информация о разработчиках',
            help='Кто разрабатывал сайт и занимался решением задач по поддержке сайта,'
                 ' по какой причине нет возможности обратиться к разработчикам сайта'),
        'another_content': fields.text(
            'Необходимо ли создавать дополнительный контент',
            help=''),
        'access_ids': fields.one2many(
            'brief.access',
            'brief_id',
            'Доступы, предоставляемые партнером',
            help=''),
        'text_content': fields.selection(
            [
                (1, 'SEO-статья'),
                (2, 'Пресс-релиз'),
                (3, 'Продающая статья'),
                (4, 'Новость'),
                (0, 'Другое'),
            ],
            'Вид текстового контента, который Вы бы хотели заказать',
            help=''),
        'text_content_another': fields.char(
            'Другое',
            size=250,
            help=''),
        'need_text': fields.text(
            'По каким услугам (направоениям) нужны тексты?',
            help=''),
        'vol_text': fields.float(
            'Приблизительный объем текста (в тысячах знаков)',
            help=''),
        'sources_seo': fields.selection(
            [
                (1, 'Разрабатывают специалисты компании UpSale'),
                (2, 'Предоставляет Ваша компания')
            ],
            'Источники ключевых запросов для SEO-текстов',
            help=''),
        'newsmaker': fields.text(
            'Информационный повод',
            help=''
        ),
        'in_silence': fields.text(
            'Темы, которые не должны затргиваться в тексте',
            help=''),
        'purpose': fields.text(
            'Основная цель текста',
            help=''),
        'what_sell': fields.text(
            'Какую услугу/товар вы хотите продать',
            help=''),
        'where': fields.text(
            'Где (на какой площадке, странице сайта) будет размещен готовый текст?',
            help=''),
        'sources_info': fields.text(
            'Укажите возможные источники информации, которые могли бы помочь в написании текста',
            help=''),
        'distinguishes': fields.text(
            'Что отличает вас от подобных компаний',
            help=''),
        'problem_resolve': fields.text(
            'Какие проблемы потребителя решает ваша услуга/товар?',
            help=''),
        'hidden_desires': fields.text(
            'Какие скрытые желания потребителя удовлетворяет ваша услуга/товар?',
            help=''),
        'benefit': fields.text(
            'Какую выгоду получит клиент, воспользовавшись услугами именно вашей компании?',
            help=''),
        'why_you': fields.text(
            'Почему вашими услугами необходимо воспользоваться прямо сейчас?',
            help=''),
        'marketing': fields.text(
            'Какими бы маркетинговыми приемами вы бы хотели привлечь/заинтересовать вашего клиента?',
            help=''),
        'transfer': fields.boolean(
            'Перенос сайта',
            help=''),
        'check_leader': fields.related(
            'services_ids',
            'check_leader',
            type='boolean',
            string='Check'),
        'sum_mediaplan': fields.float(
            "Сумма медиаплана",
            digits=(10, 2),
            required=False,
            states={'inwork': [('required', True)]},
            help='Денежная сумма медиаплана'),
        'currency': fields.selection(
            [
                ('dol', '$'),
            ],
            'Валюта',
            states={'inwork': [('required', True)]},
            help='Валюта'
        ),
        'from': fields.char("from", size=10),
        'work_state': fields.selection(
            (
                ('inwork', 'В работе'),
                ('overdue', 'Просрочен'),
            ), 'Статус', readonly=True
        ),

        'check_m': fields.function(
            _check_access,
            method=True,
            string="Проверка на менеджера продаж",
            type="boolean",
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string="Проверка на ответственного специалиста",
            type="boolean",
            invisible=True
        ),
        'check_h': fields.function(
            _check_access,
            method=True,
            string="Проверка на руководителя направления",
            type="boolean",
            invisible=True
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string="Проверка на видят всех",
            type="boolean",
            invisible=True
        ),

        'leader_ids': fields.function(
            _get_service_head,
            method=True,
            type='many2many',
            relation='res.users',
            string="Группа руководителей"
        ),
        'check_head': fields.boolean('Проверка руководителей'),
        'check_long': fields.boolean('Проверка на срыв планов'),
    }

    _defaults = {
        'state': 'draft',
        'user_id': lambda self, cr, uid, context: uid,
        'partner_id': lambda self, cr, uid, context: context.get('partner_id', False),
        'partner_name': lambda self, cr, uid, context: context.get('partner_name', False),
        'name': lambda self, cr, uid, context: context.get('name', False),
        'job_position': lambda self, cr, uid, context: context.get('job_position', False),
        'phone': lambda self, cr, uid, context: context.get('phone', False),
        'email': lambda self, cr, uid, context: context.get('email', False),
        'from': lambda self, cr, uid, context: context.get('from', False),
        'responsible_user': lambda self, cr, uid, context: uid,
        'brief_super': 142,
        'check_head': False,
        'work_state': 'inwork',
    }

    _constraints = [
        (_check_budget,
         'Необходимо указать планируемый бюджет',
         [u'Планируемый бюджет']),
        (_check_mediaplan,
         'На данном этапе должен быть добавлен Медиаплан',
         [u'Медиа-план']),
        (_check_accept,
         'Вам необходимо указать к кому относится данный бриф.',
         [u'Партнер']),
    ]

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        new_item = []
        for item in args:
            if item[0] == 'create_date':
                new_item = ['create_date', '<=', '{0} 23:59:59'.format(item[2],)]
                item[2] = '{0} 00:00:00'.format(item[2],)
                item[1] = '>='
            if item[0] == 'direction':
                item[0] = "services_ids.direction"
                item[2] = item[2].upper()
        if new_item:
            args.append(new_item)
        return super(Brief, self).search(cr, user, args, offset, limit, order, context, count)
Brief()


class BriefHistory(Model):
    _name = 'brief.history'
    _rec_name = 'us_id'

    _columns = {
        'us_id': fields.many2one('res.users', u'Перевел'),
        'cr_date': fields.datetime(u'Дата и время'),
        'state': fields.char(u'На этап', size=65),
        'state_id': fields.char(u'Этап', size=65),
        'brief_id': fields.many2one('brief.main', u'Брифа', invisible=True),
        'create_date': fields.datetime(
            'Дата и время',
            select=True,
            readonly=True
        )
    }

    _order = "create_date desc"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('accd'):
            order = "cr_date desc"
            args.append(('state', '=', 'Бриф на согласовании'))

        return super(BriefHistory, self).search(cr, uid, args, offset, limit, order, context, count)
BriefHistory()


class BriefAccess(Model):
    _name = 'brief.access'
    _rec_name = 'type'
    _columns = {
        'brief_id': fields.many2one('brief.main', u'Брифа', invisible=True),
        'type': fields.selection(
            [
                ('ftp', 'ftp'),
                ('db', 'База данных'),
                ('admin', 'Система администрирования'),
                ('hosting', 'Хостинг'),
            ], u'Доступы, предоставляемые партнером'),
        'link': fields.char(u'Ссылка', size=250),
        'login': fields.char(u'Логин', size=250),
        'pswd': fields.char(u'Пароль', size=250),
    }
BriefAccess()


class BriefManagerGroups(Model):
    _name = 'brief.manager.groups'
    _description = u"Рабочие команды менеджеров по привлечению и работе с партнерами"

    def _check_upwork_manager(self, cr, uid, ids):

        for record in self.read(cr, uid, ids, ['manager_second_lvl_id']):
            another_ids = self.search(cr, uid, [
                ('manager_second_lvl_id', '=', record['manager_second_lvl_id'][0]),
                ('id', '!=', record['id'])
            ])

            if another_ids:
                return False
            return True

    _columns = {
        'name': fields.char(u'Название группы', size=250),
        'manager_first_lvl_ids': fields.many2many(
            'res.users',
            'res_users_brief_manager_rel',
            'brief_gr_id',
            'users_id',
            string=u'Менеджеры по привлечению клиентов',
            domain="[('groups_id', 'in', [47])]"
        ),
        'manager_second_lvl_id': fields.many2one(
            'res.users',
            u'Менеджер по работе с клиентом',
            domain="[('groups_id', 'in', [48])]"
        )
    }

    _constraints = [
        (_check_upwork_manager,
         'Менеджер по привлечению не может входить в несколько групп!',
         []),
    ]
BriefManagerGroups()
