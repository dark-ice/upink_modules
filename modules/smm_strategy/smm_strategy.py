# -*- encoding: utf-8 -*-
import netsvc
from datetime import datetime, timedelta
from notify import notify
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


wf_service = netsvc.LocalService("workflow")


class smm_strategy(Model):
    _name = "smm.strategy"
    _description = u"Запуска и реализации стратегии СММ"
    _order = 'id desc'

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    def _dedline_start(self, cr, uid, ids, field_name, arg, context):
        result = {}
        obj = self.browse(cr, uid, ids[0], context=context)
        start_line = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
        if obj.pay_day and obj.prep_days > 0:
            start_date = datetime.strptime(obj.pay_day, "%Y-%m-%d %H:%M:%S")
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

    def new_view(self, cr, uid, ids, context=None):
        domain = []
        view_name = 'Форма Реализация стратении SMM'
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [
            ('name', 'like', view_name),
            ('model', '=', self._name)
        ])
        value = {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'smm.strategy',
            'view_id': view_id,
            'res_id': ids,
            'type': 'ir.actions.act_window',
            'domain': domain,
            'target': 'none'
        }
        return value

    workflow_name = 'smm.strategy.start_workflow'

    states = {
        'draft': 'черновик',
        'agreement_application': 'согласование заявки',
        'appointment_smm_spec': 'назначение СММ специалиста',
        'preparation_strategy': 'составление стратегии',
        'approval_strategy': 'утверждение стратегии',
        'completion_strategy': 'доработка стратегии',
        'introduce_strategy': 'ознакомление со стратегией',
        'start_strategy': 'запуск стратегии',
        'creat_charact_commun': 'создание персонажей и сообществ',
        'primary_filling_content': 'первичное наполнение контентом',
        'development_design': 'разработка дизайна',
        'approval_design': 'утверждение дизайна',
        'completion_design': 'доработка дизайна',
        'install_design': 'установка дизайна',
        'create_script_contest': 'создание сценария конкурса',
        'agreement_contest': 'согласование сценария',
        'start_targeting_reclam': 'запуск таргетированной рекламы',
        'start_contest': 'запуск конкурса',
        'work_on_promotion': 'работа по продвижению',
        'sending_additional_sentence': 'отправка дополнительного предложения',
        'closed': 'работы закончены',
    }

    def workflow_setter(self, cr, uid, ids, state=None):
        return self.write(cr, uid, ids, {'state': state})

    def _pay_more(self, cr, uid, ids, field_name, arg, context):
        result = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        if obj.project_cost and obj.pay_sum:
            result[obj.id] = obj.project_cost - obj.pay_sum
        return result

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
                if data.manager_work_id.id == uid or uid in users_work:
                    access += 'w'

                #  Руководитель по развитию
                group_upwork = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Продажи / Руководитель по развитию партнеров')])
                users_upwork = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_upwork)], order='id')
                if uid in users_upwork:
                    access += 'h'

                #  Руководитель направления SMM
                group_coord = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Руководитель направления SMM')])
                users_coord = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_coord)], order='id')
                if uid in users_coord:
                    access += 's'

                #  Специалист направления SMM
                if data.spec_user_id.id == uid or uid in users_coord:
                    access += 'r'

                #  Менеджер по развитию
                if data.manager_upwork_id.id == uid:
                    access += 'u'

                val = False

                letter = name[6]

                if letter in access:
                    val = True
                res[data.id] = val
        return res

    _rec_name = 'partner_id'
    _columns = {
        'state': fields.selection(zip(states.keys(), states.values()), 'статус', readonly=True),
        #Шапка
        'user_id': fields.many2one('res.users', 'Автор', select=True, readonly=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', select=True),
        'url': fields.char('Сайт партнера', size=156),

        'manager_work_id': fields.many2one('res.users', 'Менеджер по работе с партнерами', select=True),
        'manager_upwork_id': fields.related(
            'partner_id',
            'user_id',
            type="many2one",
            relation="res.users",
            string="Менеджер по развитию партнеров",
            store=False,
            readonly=True
        ),

        # Срок сотрудничества по проекту
        'date_partners_from': fields.datetime('с'),
        'date_partners_to': fields.datetime('по'),

        'targeted_advertising': fields.boolean('Таргетированная реклама'),
        'contest': fields.boolean('Конкурс'),
        'lead_management': fields.boolean('Лид менеджмент'),
        'hidden_marketing': fields.boolean('Скрытый маркетинг'),
        'reputation_management': fields.boolean('Управление репутацией'),

        'commentary': fields.text('Комментарий по доработке'),

        'spec_user_id': fields.many2one('res.users', 'Специалист', domain="[('groups_id','in',[80])]"),
        'strategy_file_id': fields.many2one('attach.files', 'Стратегия'),

        'servis_ids': fields.many2many(
            'brief.services.stage',
            'brief_services_smm_strategys_rel',
            'smm_st_id',
            'b_ser_id',
            string='Услуги',
            domain="[('usergroup','in',[137, 143])]"),

        # Данные по оплатам
        'payments_ids': fields.one2many('smm.strategy.payments', 'smm_strategy_id', 'Оплаты'),

        # Реализация стратегии
        # показатели SLA SMM
        'indicators': fields.one2many('smm.indicators.stage', 'smm_strategy_id', 'Показатели SLA SMM'),
        # итого по каждому отчетному периоду
        'total_sla_ids': fields.one2many('smm.sla.total', 'smm_strategy_id', 'Итого по каждому отчетному периоду'),

        'team_ids': fields.many2many(
            'res.users',
            'res_users_smm_strategy_rel',
            'smm_st_id',
            'users_id',
            string='Команда',
            domain="[('groups_id', 'in', [80])]"
        ),
        'reg_work_ids': fields.one2many('smm.strategy.regwork', 'smm_strategy_id', 'Регулярная работа'),
        'tz_name': fields.char('ТЗ на дизайн', size=250),
        'tz_file': fields.binary('ТЗ на дизайн'),
        'tz_file_id': fields.many2one('attach.files', 'ТЗ на дизайн'),

        'design_name': fields.char('Дизайн', size=250),
        'design_file': fields.binary('Дизайн'),
        'design_file_id': fields.many2one('ir.attachment', 'Дизайн'),
        'contes_name': fields.char('Сценарий конкурса', size=250),
        'contes_file': fields.binary('Cценарий конкурса'),
        'contes_file_id': fields.many2one('attach.files', 'Cценарий конкурса'),
        'additional_sentence_name': fields.char('Дополнительное предложение', size=250),
        'additional_sentence_file': fields.binary('Дополнительное предложение'),
        'additional_sentence_file_id': fields.many2one('ir.attachment', 'Дополнительное предложение'),
        'reason_stop_work': fields.text('Причина остановки работ'),

        # История
        'history_id': fields.one2many('smm.strategy.history', 'smm_strategy_id', 'История'),
        # Дедлайн для выполнения заданий
        'deadline': fields.datetime('Дедлайн на следующее состояние', readonly=True),

        'reports': fields.one2many('smm.strategy.reports', 'smm_id', 'Отчеты'),
        'contract_ids': fields.one2many('smm.strategy.contract', 'smm_id', 'Договор'),
        'check_w': fields.function(_check_access, method=True, string="Менеджер по работе", type="boolean", invisible=True),
        'check_u': fields.function(_check_access, method=True, string="Менеджер по развитию", type="boolean", invisible=True),
        'check_h': fields.function(_check_access, method=True, string="Руководитель по развитию", type="boolean", invisible=True),
        'check_s': fields.function(_check_access, method=True, string="Руководитель направления SMM", type="boolean", invisible=True),
        'check_r': fields.function(_check_access, method=True, string="Специалист направления SMM", type="boolean", invisible=True),
    }

    _defaults = {
        'state': 'draft',
        'user_id': lambda self, cr, uid, context: uid,
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        field = self.browse(cr, uid, ids)[0]
        next_state = values.get('state', False)
        state = field.state

        error = ''
        if next_state and next_state != state:
            #  draft -> agreement_application
            if state == 'draft' and next_state == 'agreement_application':
                if not (not (not field.targeted_advertising or values.get('targeted_advertising', False)) or not (
                    not field.contest or values.get('contest', False)) or not (
                    not field.lead_management or values.get('lead_management', False)) or not (
                    not field.hidden_marketing or values.get('hidden_marketing', False)) or not (
                    not field.reputation_management or values.get('reputation_management', False))):
                    error += 'Необходимо выбрать одно или несколько из: Таргетированная реклама, Конкурс, Лид менеджмент, Скрытый маркетинг, Управление репутацие; '

                if field.date_partners_from > field.date_partners_to:
                    error += 'Дата сотрудничества по проекту меньше начала сотрудничества; '

                if not field.servis_ids:
                    error += 'Необходимо указать услугу(и); '

                if not field.payments_ids:
                    error += 'Необходимо указать оплату'

            #  agreement_application -> appointment_smm_spec

            #  appointment_smm_spec -> preparation_strategy
            if state == 'appointment_smm_spec' and next_state == 'preparation_strategy':
                if not field.spec_user_id and not values.get('spec_user_id', False):
                    error += 'Необходимо указать специалиста; '

                if not field.team_ids:
                    error += 'Необходимо набрать команду'

            #  preparation_strategy -> approval_strategy
            if state == 'preparation_strategy' and next_state == 'approval_strategy':
                if not field.strategy_file_id:
                    error += 'Необходимо вложить файл со стратегией'

            #  approval_strategy -> completion_strategy
            if state == 'approval_strategy' and next_state == 'completion_strategy':
                if not values.get('commentary') and field.commentary:
                    error += 'Необходимо ввести комментарий по доработке'

            #  completion_strategy -> approval_strategy
            #  approval_strategy -> introduce_strategy
            #  introduce_strategy -> start_strategy

            #  creat_charact_commun -> primary_filling_content
            if state == 'creat_charact_commun' and next_state == 'primary_filling_content':
                if not field.reg_work_ids:
                    error += 'Необходимо создать запись(и) регулярных работ'

            #  primary_filling_content -> development_design
            if state == 'promary_filling_content' and next_state == 'development_design':
                if not field.tz_file_id:
                    error += 'Необходимо вложить файл с ТЗ на дизайн; '

            #  development_design -> approval_design
            if state == 'development_design' and next_state == 'approval_design':
                if not field.design_file_id:
                    error += 'Необходимо вложить файл с дизайном'

            #  approval_design -> completion_design
            #  completion_design -> approval_design
            #  approval_design -> install_design
            #  install_design -> create_script_contest
            #  create_script_contest -> agreement_contest
            if state == 'create_script_contest' and next_state == 'agreement_contest':
                if not field.contes_file_id:
                    error += 'Необходимо вложить файл со сценарием'
            #  agreement_contest -> start_contest
            #  agreement_contest -> start_targeting_reclam
            #  start_contest -> work_on_promotion
            #  start_targeting_reclam -> work_on_promotion
            #  primary_filling_content -> work_on_promotion
            #  start_contest -> start_targeting_reclam
            #  work_on_promotion -> sending_additional_sentence
            if state == 'work_on_promotion' and next_state == 'sending_additional_sentence':
                if not field.additional_sentence_file_id:
                    error += 'Необходимо вложить файл с дополнительным предложением'

            #  sending_additional_sentence -> closed
            if state == 'sending_additional_sentence' and next_state == 'closed':
                if not field.reason_stop_work:
                    error += 'Необходимо указать причину остановки работ'

        if error:
            raise osv.except_osv("SMM strategy", error)

        if next_state:
            values.update(
                {
                    'history_id': [(0, 0, {
                        'us_id': uid,
                        'cr_date': datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
                        'state': self.states[next_state]
                    })]
                })

        return super(smm_strategy, self).write(cr, uid, ids, values, context)

    def copy(self, cr, uid, id, default=None, context=None):
        default['history_id'] = None
        return super(smm_strategy, self).copy(cr, uid, id, default, context)


smm_strategy()


class smm_strategy_payments(Model):
    _name = "smm.strategy.payments"
    _description = u"Оплаты"

    _columns = {
        'sum': fields.float('Сумма оплаты'),
        'pay_currency': fields.many2one('partner.currency', 'Валюта оплаты'),
        'pay_date': fields.datetime('Дата оплаты'),
        'user_id': fields.many2one('res.users', 'Автор', readonly=True),
        'smm_strategy_id': fields.many2one('smm.strategy', 'Запуск смм стратегии', invisible=True),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }


smm_strategy_payments()


class smm_indicators_stage(Model):
    _name = "smm.indicators.stage"
    _description = u"Справочник Показатели SMM"

    def calculate(self, cr, uid, row, context=None):
        """
            Расчет показателя.
                Если найдена формула разбиваем её по разделителю ';',
                    и исполняем итерационными, затем что бы использовалось последнее условие
                По просчету округляем до двух знаков
                RETURNS float
        """
        result = 0
        fact = row.fact
        plan = row.plan
        try:
            formula_table = row.sla_id.formula.split(';')
            for formula in formula_table:
                exec formula
            result = round(result, 2) if result else False
            return result
        except ZeroDivisionError:
            raise osv.except_osv("Деление на 0", u"Вы пытаетесь делить на 0! Измените плановые показатели.")

    def _compliance_indic_mdo(self, cr, uid, ids, field_name, arg, context=None):
        """
            Одной формулой считаем выполнение
            Возвращаем float
        """
        if not context:
            context = {}
        res = {}
        row = self.browse(cr, uid, ids, context)[0]
        compliance = self.calculate(cr, uid, row, context=None)
        if not compliance:
            compliance = 0
        mbo_row = compliance * row.influence
        res[row.id] = {
            'compliance': compliance,
            'mbo': mbo_row,
        }
        TotalObj = self.pool.get('smm.sla.total')
        Tid = TotalObj.search(cr, uid,
                              [('date_id.id', '=', row.date_id.id), ('smm_strategy_id', '=', row.smm_strategy_id.id)],
                              limit=1)
        if not Tid:
            values = {'influence': row.influence,
                      'mbo': compliance * row.influence,
                      'date_id': row.date_id.id,
                      'smm_strategy_id': row.smm_strategy_id.id,
                      }
            TotalObj.create(cr, uid, values, context)
        else:
            Rid = self.search(cr, uid,
                              [('date_id.id', '=', row.date_id.id), ('smm_strategy_id', '=', row.smm_strategy_id.id)])
            Rrows = self.browse(cr, uid, Rid, context)
            influence = 0
            mbo = 0
            for r in Rrows:
                influence = influence + r.influence
                if r.id == ids[0]:
                    mbo += mbo_row
                else:
                    mbo += r.mbo

            values = {'influence': influence,
                      'mbo': mbo,
                      'smm_strategy_id': row.smm_strategy_id.id,
                      }
            TotalObj.write(cr, uid, Tid, values, context)
        return res

    _columns = {
        'date_id': fields.many2one('sla.interval.date', 'Период', required=True, select=True),
        'sla_id': fields.many2one('indicators.sla.stage', 'Показатели', required=True),
        'influence': fields.float('Вес', required=True),
        'plan': fields.float('План', required=True),
        'fact': fields.float('Факт'),
        'compliance': fields.function(_compliance_indic_mdo, type='float', method=True, store=True, string='Выполнение',
                                      multi='compliance'),
        'mbo': fields.function(_compliance_indic_mdo, type='float', method=True, store=True, string='MBO', multi='mbo'),
        'smm_strategy_id': fields.many2one('smm.strategy', 'SMM стратегия', invisible=True),
    }

    def unlink(self, cr, uid, ids, context=None):
        Rrows = self.browse(cr, uid, ids[0], context)
        TotalObj = self.pool.get('smm.sla.total')
        Tid = TotalObj.search(cr, uid, [('date_id.id', '=', Rrows.date_id.id),
                                        ('smm_strategy_id', '=', Rrows.smm_strategy_id.id)])
        Rids = self.search(cr, uid,
                           [('date_id.id', '=', Rrows.date_id.id), ('smm_strategy_id', '=', Rrows.smm_strategy_id.id)])
        if len(Rids) > 1:
            Tdata = TotalObj.browse(cr, uid, Tid[0], context)
            values = {'influence': Tdata.influence - Rrows.influence,
                      'mbo': Tdata.mbo - Rrows.mbo,
            }
            TotalObj.write(cr, uid, Tid, values, context)
        else:
            TotalObj.unlink(cr, uid, Tid, context)
        return super(smm_indicators_stage, self).unlink(cr, uid, ids[0], context)


smm_indicators_stage()


class smm_sla_total(Model):
    _name = "smm.sla.total"
    _description = u"Итого SLA показателей SMM"
    _order = "date_id desc"
    _columns = {
        'date_id': fields.many2one('sla.interval.date', 'Период', readonly=True, select=True),
        'influence': fields.float('Вес', readonly=True),
        'mbo': fields.float('MBO', readonly=True),
        'smm_strategy_id': fields.many2one('smm.strategy', 'SMM стратегия', invisible=True),
    }


smm_sla_total()


class smm_strategy_regwork(Model):
    _name = 'smm.strategy.regwork'
    _description = u'Регулярная работа'

    _columns = {
        'create_date': fields.datetime('Дата', readonly=True),
        'name': fields.text('Комментарий'),
        'user_id': fields.many2one('res.users', 'Автор', readonly=True),
        'smm_strategy_id': fields.many2one('smm.strategy', 'Запуск смм стратегии', invisible=True),
        'amount_of_work': fields.text('Объем работы', required=True),
        'hours_spent': fields.integer('Количество потраченных часов', required=True),
        'rep_file_id': fields.many2one('attach.files', 'Файл'),
        'performer': fields.many2one('res.users', 'Исполнитель', domain="[('groups_id','in',[80])]"),
        'team': fields.related(
            'smm_strategy_id',
            'team_ids',
            type='many2one',
            string='Исполнитель'),
        'date_start': fields.date("с", required=True),
        'date_end': fields.date("по", required=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }


smm_strategy_regwork()


class smm_strategy_history(Model):
    _name = 'smm.strategy.history'
    _columns = {
        'us_id': fields.many2one('res.users', 'Перевел'),
        'cr_date': fields.datetime('Дата и время'),
        'state': fields.char('На этап', size=65),
        'smm_strategy_id': fields.many2one('smm.strategy', 'Запуск смм стратегии', invisible=True),
    }

    _defaults = {
        'us_id': lambda self, cr, uid, context: uid,
        'cr_date': lambda *a: datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    }


smm_strategy_history()


class smm_strategy_contract(Model):
    _name = 'smm.strategy.contract'

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split("\\")[-1]
        return {'value': res}

    _columns = {
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'cr_date': fields.datetime('Дата и время', readonly=True),
        'rep_file_id': fields.many2one('attach.files', 'Договор'),
        'smm_id': fields.many2one('smm.strategy', 'SMM strategy', invisible=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'cr_date': lambda *a: datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    }

    _order = "create_date desc"


smm_strategy_contract()


class smm_strategy_reports(Model):
    _name = "smm.strategy.reports"
    _description = u"Справочник Отчеты"

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    _columns = {
        'create_date': fields.datetime('Дата записи', readonly=True),
        'user_id': fields.many2one('res.users', 'Автор записи', readonly=True),
        'rep_file_id': fields.many2one('attach.files', 'Отчет (файл)'),
        'comments': fields.text('Комментарий'),
        'smm_id': fields.many2one('smm.strategy', 'SMM', invisible=True),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }


smm_strategy_reports()
