# -*- encoding: utf-8 -*-
from __future__ import print_function
from osv import fields, osv
from datetime import datetime, timedelta
from notify import notify

from openerp import tools
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


class campaign_report_type(osv.osv):
    _name = "campaign.report.type"
    _description = u"Список типов отчетов для кампаний "
    _columns = {
        'name': fields.char('Тип отчета', size=156, required=True, select=True),
        'compan_type': fields.selection(
            [
                ('incoming', 'Входящая компания'),
                ('outgoing', 'Исходящая компания'),
            ], 'Тип компании', select=True),
    }

campaign_report_type()


class Campaign(osv.osv):
    _name = "campaign.template"
    _description = u'Шаблон для Исходящей и Входящих типов кампаний'
    _auto = False
    _rec_name = 'url'

    def onchange_partner(self, cr, uid, ids, field_name, context=None):
        res = {}
        autor_part = {}
        if field_name:
            rez = self.pool.get('crm.lead').search(cr, uid, [('partner_id.id', '=', field_name)], limit=1)
            if rez:
                autor_part = self.pool.get('crm.lead').read(cr, uid, rez, ['user_id'])[0]
            if autor_part:
                res['manager_work_id'] = autor_part['user_id']
        return {'value': res}

    def _dedline_start(self, cr, uid, ids, field_name, arg, context):
        result = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        start_line = datetime.now(pytz.utc)
        if obj.pay_day and obj.prep_days > 0:
            start_date = datetime.strptime(obj.pay_day, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            start_line = start_date
            count = 0
            while count < obj.prep_days:
                if datetime.weekday(start_line + timedelta(days=1)) == 5:
                    start_line = start_line + timedelta(days=3)
                elif datetime.weekday(start_line + timedelta(days=1)) == 6:
                    start_line = start_line + timedelta(days=2)
                else:
                    start_line = start_line + timedelta(days=1)
                count += 1
        result[obj.id] = start_line
        return result

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        if ids:
            data_ids = self.browse(cr, uid, ids, context)

            for data in data_ids:
                access = str()

                #  Руководитель направления CALL
                group_coord = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Руководитель направления CALL')])
                users_coord = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_coord)], order='id')
                if uid in users_coord:
                    access += 's'

                #  Супервайзер проекта
                if data.supervisor.id == uid:
                    access += 'r'

                #  Менеджеры 2 и 3
                group_work = self.pool.get('res.groups').search(cr, 1, [('name', 'in', ('Продажи / Менеджер по работе с партнерами', 'Продажи / Менеджер по развитию партнеров', 'Продажи / Руководитель по развитию партнеров', 'Продажи / Руководитель по работе с партнерами'))])
                users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_work)], order='id')
                if data.manager_upwork_id.id == uid or uid in users_work:
                    access += 'u'

                val = False

                letter = name[6]

                if letter in access:
                    val = True
                res[data.id] = val
        return res

    _columns = {
        # Шапка + Данные по оплатам
        'partner_id': fields.many2one('res.partner', 'Партнер', select=True),
        'url': fields.char('Сайт', size=156),
        'supervisor': fields.many2one(
            'res.users',
            'Супервайзер проекта',
            select=True,
            domain="[('groups_id','in',[103])]"),
        'pay_day': fields.datetime('Дата оплаты'),
        'pay_sum': fields.float('Сумма оплаты'),
        'pay_currency': fields.many2one('partner.currency', 'Валюта оплаты'),
        'prep_days': fields.integer('Количество рабочих дней на подготовку проекта'),
        'start_line': fields.function(
            _dedline_start,
            type='datetime',
            method=True,
            store=True,
            string='Дедлайн по запуску проекта',
            select=True),


        # 'report_type' : fields.many2one('template.report.type.stage', 'Тип отчета'),
        'conv_record': fields.selection(
            [
                ('yes', 'да'),
                ('no', 'нет')
            ], 'Необходимость записей разговоров'),

        'cost_currency': fields.many2one('partner.currency', 'Валюта затрат'),

        #    тех. настройка
        #'aoh': fields.char('АОН', size=15),
        #
        'settings_email': fields.text('Настройки электронной почты'),

        # ТЗ
        'tz_pattern_file_id': fields.many2one('attach.files', 'Шаблон ТЗ'),
        'tz_filled_file_id': fields.many2one('attach.files', 'Заполненное ТЗ'),
        're_tz_commentary': fields.text('Комментарии по доработке'),

        # сценарий
        'prior_scenario_file_id': fields.many2one('attach.files', 'Предварительный сценарий'),
        'scenario_file_id': fields.many2one('attach.files', 'Сценарий с дополнениями'),
        'scenario_comment': fields.text('Комментарии по доработке'),

        # Орг данные и базы данных

        're_db_commentary': fields.text('Комментарии по доработке'),
        'report_pattern_file_id': fields.many2one('attach.files', 'Шаблон формы отчета'),

        # Отчетность
        'finance_report_file_id': fields.many2one('attach.files', 'Шаблон формы отчета'),
        'datetime_fin_report': fields.datetime('Дата предоставления отчета'),
        'analytic_report_name': fields.char('Аналитический отчет', size=250),
        'analytic_report': fields.binary('Аналитический отчет'),
        'datetime_an_report': fields.datetime('Дата предоставления отчета'),
        'stat_report_name': fields.char('Статистический отчет', size=250),
        'stat_report': fields.binary('Статистический отчет'),
        'datetime_stat_report': fields.datetime('Дата предоставления отчета'),

        'add_report_name': fields.char('Дополнения к отчетам', size=250),
        'additional_report': fields.binary('Дополнения к отчетам'),
        'datetime_add_report': fields.datetime('Дата предоставления отчета'),

        # Дедлайн для выполнения заданий
        'deadline': fields.datetime('Дедлайн на следующее состояние', readonly=True),

        'manager_work_id': fields.many2one('res.users', 'Менеджер по работе с партнерами', select=True),
        'manager_upwork_id': fields.related('partner_id', 'user_id', type="many2one", relation="res.users", string="Менеджер по развитию партнеров", store=False, readonly=True),

        'check_s': fields.function(_check_access, method=True, string="Руководитель направления CALL", type="boolean", invisible=True),
        'check_r': fields.function(_check_access, method=True, string="Супервайзер проекта", type="boolean", invisible=True),
        'check_u': fields.function(_check_access, method=True, string="Менеджер по развитию", type="boolean", invisible=True),

    }

Campaign()


class OutCampaign(osv.osv):
    _name = 'out.campaign'
    _inherit = 'campaign.template'
    _description = u'Исходящие кампании. Содержит только поля, которые отличаются от Входящих'
    _auto = True
    _order = "create_date desc"
    _log_access = True

    def new_view(self, cr, uid, ids, context=None):
        view_name = 'Реализация проекта'
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', view_name), ('model', '=', self._name)])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'views': [(view_id[0], 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
            'res_id': ids[0],
        }

    workflow_name = 'out.campaign.start_compan_out'

    states = {
        'draft': 'черновик',
        'preparation_template': 'подготовка шаблона ТЗ',
        'sent_template_to_manager': 'шаблон ТЗ отправлен менеджеру',
        'filling_tz': 'заполнение ТЗ',
        'agreement_tz': 'согласование ТЗ',
        'tz_on_completion': 'ТЗ на доработке',
        'preparation_screenplay': 'подготовка сценария',
        'approval_screenplay': 'утверждение сценария',
        'screenplay_on_completion': 'сценарий на доработку',
        'preparation_contact_basa': 'подготовка контактной базы',
        'approval_contact_basa': 'согласование контактной базы',
        'contact_basa_on_completion': 'контактная база на доработке',
        'preparation_report_form': 'подготовка формы отчета',
        'approval_report_form': 'согласование формы отчета',
        'report_form_on_completion': 'форма отчета на доработке',
        'training_agents': 'обучение агентов',
        'testing_agents_partner': 'тестирование агентов партнером',
        'teh_configuring_project': 'тех. настройка проекта',
        'coordination_organ_quaeres': 'согласование орг. вопросов',
        'project_implementation': 'реализация проекта',
        'agreement_reporting': 'согласование отчетности',
        'closed': 'проект завершен',
    }

    def workflow_setter(self, cr, uid, ids, state=None):
        return self.write(cr, uid, ids, {'state': state})

    def action_db(self, cr, uid, ids):
        return self.write(cr, uid, ids, {'state': 'approval_contact_basa'})

    def _pay_more(self, cr, uid, ids, field_name, arg, context):
        result = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        if obj.project_cost and obj.pay_sum:
            result[obj.id] = obj.project_cost - obj.pay_sum
        return result

    _columns = {
        'state': fields.selection(zip(states.keys(), states.values()), u'статус', readonly=True),

        # ТЗ
        'files_id': fields.one2many('campaign.multiple.files', 'out_campaign_id', u'Доработка ТЗ'),

        'report_type': fields.many2one('campaign.report.type', u'Тип отчетности', domain=['|', ('compan_type', '=', 'outgoing'), ('compan_type', '=', False)]),

        # Отчетность
        'comments_id': fields.one2many('reports.comments', 'out_campaign_id', u'Комментарии и вопросы'),

        # Шапка
        'extra_pay': fields.function(_pay_more, type='float', method=True,
                                     store=True, string=u'Доплата по проекту'),
        'extra_pay_day': fields.datetime(u'Дата доплаты'),
        'project_cost': fields.float(u'Стоимость проекта'),
        'project_duration': fields.integer(u'Плановая продолжительность проекта (кол-во дней)'),

        #Тех настройка
        'proj_tels_id': fields.one2many('project.tels', 'out_campaign_id', u'Внутренние номера проекта'),

        # Сценарии
        'distrib_name': fields.char(u'Материалы для рассылки', size=250),
        'distrib_file': fields.binary(u'Материалиы для рассылки'),
        'distrib_file_id': fields.many2one('attach.files', u'Материалы для рассылки'),

        # Базы данных
        'db_type': fields.selection([
            ('partner', 'партнер'),
            ('upsale', 'Upsale'), ], u'Тип базы данных'),
        'db_file_name': fields.char(u'База данных по проекту', size=250),
        'db_file': fields.binary(u'База данных по проекту'),
        'db_file_id': fields.many2one('attach.files', u'База данных по проекту'),
        'contact_num': fields.integer(u'Количество контактов'),
        'aoh': fields.one2many('campaign.aoh', 'out_campaign_id', u'АОН'),
        # SLA
        # статистика звонков
        'sla_calls_ids': fields.one2many('statist.colls.stage', 'out_campaign_id', u'Статистика звонков'),
        # показатели SLA проекта
        'sla_project_ids': fields.one2many('indicator.project.stage', 'out_campaign_id', u'Показатели SLA CALL'),
        # итого по каждому отчетному периоду
        'total_sla_project_ids': fields.one2many('indicator.project.total', 'out_campaign_id', u'Итого по каждому отчетному периоду'),
        # показатели SLA агентов
        'sla_agent_ids': fields.one2many('indicator.agent.stage', 'out_campaign_id', u'Показатели SLA агентов'),
        # обучение
        'employees_for_training_ids': fields.many2many('hr.employee', 'hr_empl_out_comp_training_rel',
                                                       'out_comp_id', 'hr_employee_id', string='Список сотрудников для обучения', select=True),
        'employees_aprov_partner_ids': fields.many2many('hr.employee', 'hr_empl_out_comp_aprov_rel',
                                                        'out_comp_id', 'hr_employee_id', string='Список утвержденных партнером сотрудников', select=True, domain="[('id','in',employees_for_training_ids[0][2])]"),
        'reports': fields.one2many('campaign.reports', 'out_campaign_id', 'Отчеты'),

        'history_ids': fields.one2many('campaign.history', 'out_campaign_id', 'История'),
        'message_ids': fields.one2many('campaign.messages', 'out_campaign_id', 'Переписка по проекту'),

    }

    _defaults = {
        'state': 'draft',
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        field = self.browse(cr, uid, ids)[0]

        state = field.state
        next_state = values.get('state', False)
        error = ''
        if next_state and next_state != state:
            #  draft -> preparation_template
            #  preparation_template -> sent_template_to_manager
            if state == 'preparation_template' and next_state == 'sent_template_to_manager':
                if not field.tz_pattern_file_id:
                    error += u'Необходимо вложить файл с шаблоном ТЗ'

            #  sent_template_to_manager -> filling_tz
            #  filling_tz -> agreement_tz
            if state == 'filling_tz' and next_state == 'agreement_tz':
                if not field.tz_filled_file_id:
                    error += u'Необходимо вложить файл с заполненным ТЗ; '

                if not field.aoh:
                    error += u'Необходимо ввести АОН; '

            #  agreement_tz -> tz_on_completion
            if state == 'agreement_tz' and next_state == 'tz_on_completion':
                if not field.re_tz_commentary and not values.get('re_tz_commentary', False):
                    error += u'Необходимо заполнить комментарий по доработке ТЗ'

            #  tz_on_completion -> agreement_tz
            if state == 'tz_on_completion' and next_state == 'agreement_tz':
                if not field.files_id:
                    error += u'Необходимо вложить файл доработки ТЗ'

            #  agreement_tz -> preparation_screenplay
            #  preparation_screenplay -> approval_screenplay
            if state == 'preparation_screenplay' and next_state == 'approval_screenplay':
                if not field.prior_scenario_file_id:
                    error += u'Необходимо вложить файл с предварительным сценарием'
                if not field.employees_for_training_ids:
                    error += u'Необходимо ввести cписок сотрудников для обучения'
            
            #  approval_screenplay -> screenplay_on_completion
            if state == 'approval_screenplay' and next_state == 'screenplay_on_completion':
                if not field.scenario_comment:
                    error += u'Необходимо ввести комментарии по доработке сценария'

            #  screenplay_on_completion -> approval_screenplay
            if state == 'screenplay_on_completion' and next_state == 'approval_screenplay':
                if not field.scenario_file_id:
                    error += u'Необходимо влажить файл сценария с дополнениями'

            #  approval_screenplay -> training_agents
            #  training_agents -> testing_agents_partner
            if state == 'training_agents' and next_state == 'testing_agents_partner':
                if not field.employees_aprov_partner_ids:
                    error += u'Необходимо ввести список утвержденных партнером сотрудников'
            #  testing_agents_partner -> training_agents
            #  testing_agents_partner -> teh_configuring_project
            #  teh_configuring_project -> preparation_report_form
            if state == 'teh_configuring_project' and next_state == 'preparation_report_form':
                if not field.proj_tels_id:
                    error += u'Необходимо ввести внутренние номера проекта; '

                if not field.settings_email and not values.get('settings_email', False):
                    error += u'Необходимо ввести настройки электронной почты; '
                if not field.logic_cols and not values.get('logic_cols', False):
                    error += u'Необходимо ввести алгоритм распределения звонков в очереди; '

                if not field.turn_proj and not values.get('turn_proj', False):
                    error += u'Необходимо ввести очереди по проекту'
            
            #  preparation_report_form -> approval_report_form
            if state == 'preparation_report_form' and next_state == 'approval_report_form':
                if not field.report_pattern_file_id:
                    error += u'Необходимо вложить файл с шаблоном формы отчета'
            
            #  approval_report_form -> on_completion_report_form
            if state == 'approval_report_form' and next_state == 'on_completion_report_form':
                if not field.re_db_commentary and not values.get('re_db_commentary', False):
                    error += u'Необходимо ввести комментарий на доработку отчета'
            
            #  on_completion_report_form -> approval_report_form
            #  approval_report_form -> coordination_organ_quaere
            if state == 'approval_report_form' and next_state == 'coordination_organ_quaere':
                if not field.report_type and not values.get('report_type', False):
                    error += u'Необходимо заполнить тип отчетности; '

                if not field.conv_record and not values.get('conv_record', False):
                    error += u'Необходимо заполнить необходимость записей разговоров; '
            
            #  coordination_organ_quaeres -> project_implementation
            #  project_implementation -> agreement_reporting
            if state == 'project_implementation' and next_state == 'agreement_reporting':
                pass
            
            #  agreement_reporting -> project_implementation
            #  agreement_reporting -> closed
            #  closed -> agreement_reporting

            if error:
                raise osv.except_osv(u"Исходящая кампания", error)

            if next_state:
                values.update({'history_ids': [(0, 0, {
                    'usr_id': uid,
                    'state': self.states[next_state],
                    'state_id': next_state})]})

        return super(OutCampaign, self).write(cr, uid, ids, values, context)

OutCampaign()


class InCampaign(osv.osv):
    _name = 'in.campaign'
    _inherit = 'campaign.template'
    _description = u'Входящие кампании. Содержит только поля, которые отличаются от Исходящих'
    _auto = True
    _order = "create_date desc"

    def new_view(self, cr, uid, ids, context=None):
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'Реализация проекта'), ('model', '=', self._name)])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'views': [(view_id[0], 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
            'res_id': ids[0],
        }

    workflow_name = 'in.campaign.start_copan_incum'

    states = {'draft': 'черновик',
              'preparation_template': 'подготовка шаблона ТЗ',
              'sent_template_to_manager': 'шаблон ТЗ отправлен менеджеру',
              'filling_tz': 'заполнение ТЗ',
              'agreement_tz': 'согласование ТЗ',
              'tz_on_completion': 'ТЗ на доработке',
              'preparation_screenplay': 'подготовка сценария',
              'approval_screenplay': 'утверждение сценария',
              'screenplay_on_completion': 'сценарий на доработку',
              'preparation_contact_basa': 'подготовка контактной базы',
              'approval_contact_basa': 'согласование контактной базы',
              'contact_basa_on_completion': 'контактная база на доработке',
              'preparation_report_form': 'подготовка формы отчета',
              'approval_report_form': 'согласование формы отчета',
              'report_form_on_completion': 'форма отчета на доработке',
              'training_agents': 'обучение агентов',
              'testing_agents_partner': 'тестирование агентов партнером',
              'teh_configuring_project': 'тех. настройка проекта',
              'coordination_organ_quaeres': 'согласование орг. вопросов',
              'project_implementation': 'реализация проекта',
              'agreement_reporting': 'согласование отчетности',
              'closed': 'проект завершен',
              }

    days = (
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресение')
    )

    def workflow_setter(self, cr, uid, ids, state=None, workflow='launch'):
        return self.write(cr, uid, ids, {'state': state})

    def _pay_more(self, cr, uid, ids, field_name, arg, context):
        result = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        if obj.project_cost and obj.pay_sum:
            result[obj.id] = obj.project_cost - obj.pay_sum
        return result

    _columns = {
        'state': fields.selection(zip(states.keys(), states.values()), 'статус', readonly=True),
        # Тз
        #'files_id': fields.one2many('campaign.multiple.files', 'in_campaign_id', 'Доработка ТЗ'),
        'files_id': fields.one2many('attach.files', 'obj_id', 'Доработка ТЗ'),

        # Отчетность
        'comments_id': fields.one2many('reports.comments', 'in_campaign_id', 'Комментарии и вопросы'),

        # Шапка
        'cost_in_month': fields.float('Стоимость проекта в месяц'),
        'sum_next_pay': fields.float('Сумма следующего платежа'),
        'date_next_pay': fields.datetime('Дата следующего платежа'),
        'interval_pay': fields.char('Периодичность оплаты', size=156),

        'report_type': fields.many2one('campaign.report.type', 'Тип отчетности', domain=['|', ('compan_type', '=', 'incoming'), ('compan_type', '=', False)]),

        # Организационные данные
        'aprov_to_outcolls': fields.selection([
            ('yes', 'да'),
            ('no', 'нет'), ], 'Разрешение на исходящие звонки'),

        'number': fields.one2many('in.campaign.number', 'campaign_id', 'Номер'),
        'aoh': fields.one2many('campaign.aoh', 'in_campaign_id', 'АОН'),

        # Сценарии
        'faq_name': fields.char('ЧаВО', size=250),
        'faq': fields.binary('ЧаВо'),

        # Тех настройка ADD
        'proj_tels_id': fields.one2many('project.tels', 'in_campaign_id', 'Внутренние номера проекта'),
        'logic_cols': fields.text('Алгоритм распределения звонков в очереди'),
        'turn_proj': fields.text('Очереди по проекту'),

        # SLA
        # статистика звонков
        'sla_calls_ids': fields.one2many('statist.colls.stage', 'in_campaign_id', 'Статистика звонков'),
        # показатели SLA проекта
        'sla_project_ids': fields.one2many('indicator.project.stage', 'in_campaign_id', 'Показатели SLA CALL'),
        # итого по каждому отчетному периоду
        'total_sla_project_ids': fields.one2many('indicator.project.total', 'in_campaign_id', 'Итого по каждому отчетному периоду'),
        # показатели SLA агентов
        'sla_agent_ids': fields.one2many('indicator.agent.stage', 'in_campaign_id', 'Показатели SLA агентов'),
        # обучение
        'employees_for_training_ids': fields.many2many('hr.employee', 'hr_empl_in_camp_tran_rel',
                                                       'in_camp_id', 'hr_employee_id', string='Список сотрудников для обучения', select=True),
        'employees_aprov_partner_ids': fields.many2many('hr.employee', 'hr_empl_in_camp_aprov_rel',
                                                        'in_camp_id', 'hr_employee_id', string='Список утвержденных партнером сотрудников', select=True, domain="[('id','in',employees_for_training_ids[0][2])]"),

        'contract_ids': fields.one2many('campaign.contract', 'in_campaign_id', 'Договор'),
        'reports': fields.one2many('campaign.reports', 'in_campaign_id', 'Отчеты'),
        'schedule': fields.one2many('in.campaign.schedule', 'in_campaign_id', 'Расписание'),

        'history_ids': fields.one2many('campaign.history', 'in_campaign_id', 'История'),
        'message_ids': fields.one2many('campaign.messages', 'in_campaign_id', 'Переписка по проекту'),
    }
    _defaults = {
        'state': 'draft',
    }

    def _create_sc_items(self, cr, uid, campaign):
        schedule_pool = self.pool.get('in.campaign.schedule')
        sc_items_ids = schedule_pool.search(cr, uid, [('in_campaign_id', '=', campaign)])

        if not sc_items_ids:
            for day in self.days:
                schedule_pool.create(cr, 1, {'name': day[1], 'day_no': day[0], 'in_campaign_id': campaign}, {})

    def create(self, cr, uid, values, context=None):
        id = super(InCampaign, self).create(cr, uid, values, context)
        self._create_sc_items(cr, uid, id)
        return id

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        field = self.browse(cr, uid, ids)[0]

        self._create_sc_items(cr, uid, field.id)
        state = field.state
        next_state = values.get('state', False)
        error = ''
        if next_state and next_state != state:
            #  draft -> preparation_template
            #  preparation_template -> sent_template_to_manager
            if state == 'preparation_template' and next_state == 'sent_template_to_manager':
                if not field.tz_pattern_file_id:
                    error += 'Необходимо вложить файл с шаблоном ТЗ'

            #  sent_template_to_manager -> filling_tz
            #  filling_tz -> agreement_tz
            if state == 'filling_tz' and next_state == 'agreement_tz':
                if not field.tz_filled_file_id:
                    error += 'Необходимо вложить файл с заполненным ТЗ; '

                if not field.aoh:
                    error += 'Необходимо ввести АОН; '

            #  agreement_tz -> tz_on_completion
            if state == 'agreement_tz' and next_state == 'tz_on_completion':
                if not field.re_tz_commentary and not values.get('re_tz_commentary', False):
                    error += 'Необходимо заполнить комментарий по доработке ТЗ'
            
            #  tz_on_completion -> agreement_tz
            if state == 'tz_on_completion' and next_state == 'agreement_tz':
                if not field.files_id:
                    error += 'Необходимо вложить файл доработки ТЗ'

            #  agreement_tz -> preparation_screenplay
            #  preparation_screenplay -> approval_screenplay
            if state == 'preparation_screenplay' and next_state == 'approval_screenplay':
                if not field.prior_scenario_file_id:
                    error += 'Необходимо вложить файл с предварительным сценарием'
                if not field.employees_for_training_ids:
                    error += 'Необходимо ввести cписок сотрудников для обучения'
            
            #  approval_screenplay -> screenplay_on_completion
            if state == 'approval_screenplay' and next_state == 'screenplay_on_completion':
                if not field.scenario_comment:
                    error += 'Необходимо ввести комментарии по доработке сценария'

            #  screenplay_on_completion -> approval_screenplay
            if state == 'screenplay_on_completion' and next_state == 'approval_screenplay':
                if not field.scenario:
                    error += 'Необходимо влажить файл сценария с дополнениями'

            #  approval_screenplay -> training_agents
            #  training_agents -> testing_agents_partner
            if state == 'training_agents' and next_state == 'testing_agents_partner':
                if not field.employees_aprov_partner_ids:
                    error += 'Необходимо ввести список утвержденных партнером сотрудников'
            
            #  testing_agents_partner -> training_agents
            #  testing_agents_partner -> teh_configuring_project
            #  teh_configuring_project -> preparation_report_form
            if state == 'teh_configuring_project' and next_state == 'preparation_report_form':
                if not field.proj_tels_id:
                    error += 'Необходимо ввести внутренние номера проекта; '

                if not field.settings_email and not values.get('settings_email', False):
                    error += 'Необходимо ввести настройки электронной почты; '
                if not field.logic_cols and not values.get('logic_cols', False):
                    error += 'Необходимо ввести алгоритм распределения звонков в очереди; '

                if not field.turn_proj and not values.get('turn_proj', False):
                    error += 'Необходимо ввести очереди по проекту'
            
            #  preparation_report_form -> approval_report_form
            if state == 'preparation_report_form' and next_state == 'approval_report_form':
                if not field.report_pattern_file_id:
                    error += 'Необходимо вложить файл с шаблоном формы отчета'
            
            #  approval_report_form -> on_completion_report_form
            if state == 'approval_report_form' and next_state == 'on_completion_report_form':
                if not field.re_db_commentary and not values.get('re_db_commentary', False):
                    error += 'Необходимо ввести комментарий на доработку отчета'
            
            #  on_completion_report_form -> approval_report_form
            #  approval_report_form -> coordination_organ_quaere
            if state == 'approval_report_form' and next_state == 'coordination_organ_quaere':
                if not field.report_type and not values.get('report_type', False):
                    error += 'Необходимо заполнить тип отчетности; '

                if not field.conv_record and not values.get('conv_record', False):
                    error += 'Необходимо заполнить необходимость записей разговоров; '
            
            #  coordination_organ_quaeres -> project_implementation
            #  project_implementation -> agreement_reporting
            if state == 'project_implementation' and next_state == 'agreement_reporting':
                if not field.cost_in_month and not values.get('cost_in_month', False):
                    error += 'Необходимо ввести cтоимость проекта в месяц; '
                if not field.sum_next_pay and not values.get('sum_next_pay', False):
                    error += 'Необходимо ввести сумму следующего платежа; '
                if not field.date_next_pay and not values.get('date_next_pay', False):
                    error += 'Необходимо ввести дату следующего платежа; '

                if not field.interval_pay and not values.get('interval_pay', False):
                    error += 'Необходимо ввести периодичность оплаты; '
            
            #  agreement_reporting -> project_implementation
            #  agreement_reporting -> closed
            #  closed -> agreement_reporting

            if error:
                raise osv.except_osv("Входящая кампания", error)

            if next_state:
                values.update({'history_ids': [(0, 0, {
                               'usr_id': uid,
                               'state': self.states[next_state],
                               'state_id': next_state})]})

        return super(InCampaign, self).write(cr, uid, ids, values, context)

InCampaign()


class CampaignRelations(osv.osv):
    _name = 'campaign.relations'
    _description = u'Объект Template для хранения общих полей для one2many связей'

    _columns = {
        'in_campaign_id': fields.many2one('in.campaign', 'Входящая кампания', invisible=True),
        'out_campaign_id': fields.many2one('out.campaign', 'Исходящая кампания', invisible=True),
    }

    _auto = False

CampaignRelations()


class CampaignInnerTels(osv.osv):
    _name = "project.tels"
    _description = u"Внутренние номера проекта"
    _inherit = 'campaign.relations'
    _auto = True

    _columns = {
        'name': fields.char('Номер', size=56, required=True, select=True),
    }

CampaignInnerTels()


class CampaignReportsComments(osv.osv):
    _name = 'reports.comments'
    _description = u'Объект для хранения множества комментариев по отчетностям'
    _inherit = 'campaign.relations'
    _auto = True

    _columns = {
        'create_date': fields.datetime('Дата', readonly=True),
        'name': fields.char('Комментарий или вопрос', size=256, required=True),
    }

CampaignReportsComments()


class CampaignMultipleFiles(osv.osv):
    _name = 'campaign.multiple.files'
    _description = u'Каталог файлов привязанные к сторонним Id'
    _inherit = 'campaign.relations'
    _auto = True

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    _columns = {
        'file_name': fields.char('Имя файла', size=250),
        'file': fields.binary('Файл'),
    }

    def _check_file(self, cr, uid, ids):
        field = self.browse(cr, uid, ids[0])
        if not field.file:
            return False
        return True
    
    _constraints = [
        (_check_file,
         'Необходимо вложить файл',
         ['file']),
    ]

CampaignMultipleFiles()


class statist_colls_stage(osv.osv):
    _name = "statist.colls.stage"
    _description = u"Справочник SLA статистика звонков"
    _inherit = 'campaign.relations'
    _auto = True
    _order = "create_date desc"

    _columns = {
        'datetime_call': fields.datetime('Дата и время звонка'),
        'agent_id': fields.many2one('hr.employee', 'Агент'),
        'comment': fields.text('Комментарии'),
        'call_sla': fields.integer('SLA разговора (%)'),
    }

statist_colls_stage()


class indicator_project_stage(osv.osv):
    _name = "indicator.project.stage"
    _description = u"Справочник SLA показателей CALL"
    _inherit = 'campaign.relations'
    _auto = True
    _order = "create_date desc"

    def calculate(self, cr, uid, row, context=None):
        """
            Расчет показателя.
                Если найдена формула разбиваем её по разделителю ';',
                    и исполняем итерационными, затем что бы использовалось последнее условие
                По просчету округляем до двух знаков
                RETURNS float
        """
        plan = row.plan
        fact = row.fact
        result = 0
        try:
            formula_table = row.sla_id.formula.split(';')
            for formula in formula_table:
                exec formula
            result = round(result, 2) if result else False
            return result
        except ZeroDivisionError:
            raise osv.except_osv(u"Показатели SLA", u"Вы пытаетесь делить на 0! Измените плановые показатели.")

    def _compliance_indic_mdo(self, cr, uid, ids, field_name, arg, context=None):
        """
            Одной формулой считаем выполнение
            Возвращаем float
        """
        if context is None:
            context = {}
        res = {}
        row = self.browse(cr, uid, ids[0], context)
        compliance = self.calculate(cr, uid, row, context=None)
        if not compliance:
            compliance = 0
        mbo_row = compliance * row.influence
        res[row.id] = {
            'compliance': compliance,
            'mbo': mbo_row,
        }
        TotalObj = self.pool.get('indicator.project.total')
        Tid = TotalObj.search(cr, uid, [('date_id.id', '=', row.date_id.id), ('out_campaign_id', '=', row.out_campaign_id.id), ('in_campaign_id', '=', row.in_campaign_id.id)], limit=1)
        if not Tid:
            values = {'influence': row.influence,
                      'mbo': compliance * row.influence,
                      'date_id': row.date_id.id,
                      }
            if context.get('relize_out', False):
                values.update({
                    'out_campaign_id': row.out_campaign_id.id,
                })
            elif context.get('relize_inp', False):
                values.update({
                    'in_campaign_id': row.in_campaign_id.id,
                })
            TotalObj.create(cr, uid, values, context)
        else:
            Rid = self.search(cr, uid, [('date_id.id', '=', row.date_id.id), ('out_campaign_id', '=', row.out_campaign_id.id), ('in_campaign_id', '=', row.in_campaign_id.id)])
            Rrows = self.browse(cr, uid, Rid, context)
            influence = 0
            mbo = 0
            for r in Rrows:
                influence = influence + r.influence
                if r.id == ids[0]:
                    mbo += mbo_row
                else:
                    mbo += r.mbo

            values = {
                'influence': influence,
                'mbo': mbo,
            }
            if context.get('relize_out', False):
                values.update({
                    'out_campaign_id': row.out_campaign_id.id,
                })
            elif context.get('relize_inp', False):
                values.update({
                    'in_campaign_id': row.in_campaign_id.id,
                })
            TotalObj.write(cr, uid, Tid, values, context)
        return res

    _columns = {
        'date_id': fields.many2one('sla.interval.date', 'Период', required=True, select=True),
        'sla_id': fields.many2one('indicators.sla.stage', 'Показатели', required=True),
        'influence': fields.float('Вес', required=True),
        'plan': fields.float('План', required=True),
        'fact': fields.float('Факт'),
        'compliance': fields.function(_compliance_indic_mdo, type='float', method=True,
                                      store=True, string='Выполнение', multi='compliance'),
        'mbo': fields.function(_compliance_indic_mdo, type='float', method=True,
                               store=True, string='MBO', multi='mbo'),
    }

    def unlink(self, cr, uid, ids, context=None):
        Rrows = self.browse(cr, uid, ids[0], context)
        TotalObj = self.pool.get('indicator.project.total')
        Tid = TotalObj.search(cr, uid, [('date_id.id', '=', Rrows.date_id.id), ('out_campaign_id', '=', Rrows.out_campaign_id.id), ('in_campaign_id', '=', Rrows.in_campaign_id.id)])
        Rids = self.search(cr, uid, [('date_id.id', '=', Rrows.date_id.id), ('out_campaign_id', '=', Rrows.out_campaign_id.id), ('in_campaign_id', '=', Rrows.in_campaign_id.id)])
        if len(Rids) > 1:
            Tdata = TotalObj.browse(cr, uid, Tid[0], context)
            values = {'influence': Tdata.influence - Rrows.influence,
                      'mbo': Tdata.mbo - Rrows.mbo,
                      }
            TotalObj.write(cr, uid, Tid, values, context)
        else:
            TotalObj.unlink(cr, uid, Tid, context)
        return super(indicator_project_stage, self).unlink(cr, uid, ids[0], context)

indicator_project_stage()


class indicator_project_total(osv.osv):
    _name = "indicator.project.total"
    _description = u"Итого SLA показателей CALL"
    _inherit = 'campaign.relations'
    _auto = True

    _columns = {
        'date_id': fields.many2one('sla.interval.date', 'Период', readonly=True, select=True),
        'influence': fields.float('Вес', readonly=True),
        'mbo': fields.float('MBO', readonly=True),
    }

indicator_project_total()


class indicator_agent_stage(osv.osv):
    _name = "indicator.agent.stage"
    _description = u"Справочник SLA показателей агентов"
    _inherit = 'campaign.relations'
    _auto = True

    _columns = {
        'datetime': fields.datetime('Дата'),
        'agent_id': fields.many2one('hr.employee', 'Агент'),
        'sla_id': fields.many2one('indicators.sla.stage', 'Показатели'),
        'call_sla': fields.integer('SLA разговора (%)'),
    }

indicator_agent_stage()


class campaign_aoh(osv.osv):
    _name = "campaign.aoh"
    _columns = {
        'name': fields.char("AOH", size=15),
        'in_campaign_id': fields.many2one('in.campaign', 'Campaign', invisible=True),
        'out_campaign_id': fields.many2one('out.campaign', 'Campaign', invisible=True),
    }

campaign_aoh()


class in_campaign_number(osv.osv):
    _name = "in.campaign.number"
    _columns = {
        'name': fields.char("Кто предложил", size=256),
        'code': fields.integer("Код номера"),
        'no': fields.integer("Номер"),
        'campaign_id': fields.many2one('in.campaign', 'Campaign', invisible=True),
    }

in_campaign_number()


class campaign_contract(osv.osv):
    _name = 'campaign.contract'

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split("\\")[-1]
        return {'value': res}

    _columns = {
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'cr_date': fields.datetime('Дата создания', readonly=True),
        'rep_file_id': fields.many2one('attach.files', 'Договор'),
        'in_campaign_id': fields.many2one('in.campaign', 'Campaign', invisible=True),
    }

    _rec_name = 'cr_date'

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'cr_date': lambda *a: datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    }

    _order = "create_date desc"

campaign_contract()


class campaign_reports(osv.osv):
    _name = "campaign.reports"
    _description = u"Справочник Отчеты"

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    _columns = {
        'create_date': fields.datetime('Дата записи', readonly=True),
        'rep_file_id': fields.many2one('attach.files', 'Отчет'),
        'user_id': fields.many2one('res.users', 'Автор записи', readonly=True),
        'in_campaign_id': fields.many2one('in.campaign', 'Campaign', invisible=True),
        'out_campaign_id': fields.many2one('out.campaign', 'Campaign', invisible=True),
        'type': fields.selection([
            ('0', ''),
            ('finance', 'Финансовый отчет'),
            ('analitic', 'Аналитический отчет'),
            ('static', 'Статистический отчет'),
            ('total', 'Общий отчет'),
        ], 'Тип отчета'),
        'date_to': fields.datetime('дата предоставления отчета'),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'type': lambda *a: 0,
        'date_to': datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    _order = "create_date desc"

campaign_reports()


class in_campaign_schedule(osv.osv):
    _name = "in.campaign.schedule"

    _columns = {
        'name': fields.char("День недели", size=100),
        'day_no': fields.integer("Номер дня", invisible=True),
        'start_date': fields.datetime("Время начала"),
        'end_date': fields.datetime("Время окончания"),
        'in_campaign_id': fields.many2one('in.campaign', 'Campaign', invisible=True),
    }

    _order = "day_no"

in_campaign_schedule()


class campaign_history(osv.osv):
    _name = 'campaign.history'
    _columns = {
        'usr_id': fields.many2one('res.users', 'Перевел'),
        'create_date': fields.datetime('Дата создания'),
        'state': fields.char('На этап', size=65),
        'state_id': fields.char('Этап', size=65),
        'in_campaign_id': fields.many2one('in.campaign', 'campaign', invisible=True),
        'out_campaign_id': fields.many2one('out.campaign', 'campaign', invisible=True),
    }

    _order = "create_date desc"

campaign_history()


class campaign_messages(osv.osv):
    _name = 'campaign.messages'

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    _columns = {
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'cr_date': fields.datetime('Дата создания', readonly=True),
        'text': fields.text('Комментарий'),
        'rep_file_id': fields.many2one('attach.files', 'Файл'),
        'in_campaign_id': fields.many2one('in.campaign', 'campaign', invisible=True),
        'out_campaign_id': fields.many2one('out.campaign', 'campaign', invisible=True),
    }

    _rec_name = 'cr_date'

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'cr_date': datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    _order = "cr_date desc"

campaign_messages()
