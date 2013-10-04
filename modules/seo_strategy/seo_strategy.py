# -*- encoding: utf-8 -*-
from osv import fields, osv
from datetime import datetime
from notify import notify
from openerp import tools
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


class seo_strategys(osv.osv):
    _name = "seo.strategys"
    _description = u"Разработка и реализация SEO стратегии"
    _order = "create_date desc"
    _rec_name = 'site'

    workflow_name = 'seo.strategys.seo_strategys'

    state_first = {
        'draft': 'черновик',
        'approval_application_start': 'согласование заявки на запуск',
        'appointment_responsible': 'назначение ответственного',
        'preparation_strategy': 'составление стратегии',
        'adoption_strategy': 'утверждение стратегии',
        'completion_strategy': 'доработка стратегии',
        'appointment_executive': 'назначение исполнителя',
        'implementation_strategy': 'реализация стратегии',
        'strategy_analysis': 'анализ стратегии',
        'closed': 'работы закончены',
    }

    def _get_debt(self, cr, uid, ids, field_name, arg, context):
        result = {}
        sum_debt = 0.0
        obj_ids = self.pool.get('seo.strategys.payments.stage').search(cr, uid, [('seo_strategys_id.id', '=', ids[0])])
        if obj_ids:
            for res in self.pool.get('seo.strategys.payments.stage').browse(cr, uid, obj_ids, context=context):
                sum_debt += res.debt_pay
            result[ids[0]] = sum_debt
        return result

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename and field_name:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

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

    def workflow_setter(self, cr, uid, ids, state=None):
        return self.write(cr, uid, ids, {'state': state})

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
                group_work = self.pool.get('res.groups').search(cr, 1, [('id', 'in', (48, 77, 50, 85, 89))])
                users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_work)], order='id')
                if data.manager_work_id.id == uid or uid in users_work:
                    access += 'w'

                #  Руководители по развитию определяют ответственного
                group_upwork = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Продажи / Руководитель по развитию партнеров')])
                users_upwork = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_upwork)], order='id')
                if uid in users_upwork:
                    access += 'h'

                #  Руководитель направления SEO
                group_coord = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Руководитель направления SEO')])
                users_coord = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_coord)], order='id')
                if uid in users_coord:
                    access += 's'

                #  Специалист направления SEO
                if data.respon_user_id.id == uid or uid in users_coord:
                    access += 'r'

                #  SEO оптимизатор
                if data.executive_user_id.id == uid or uid in users_coord:
                    access += 'o'

                #res[data.id] = access

                val = False

                letter = name[6]

                if letter in access:
                    val = True
                res[data.id] = val
        return res

    def _check_p(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        if ids:
            data_ids = self.browse(cr, uid, ids, context)

            for data in data_ids:
                access = str()

                #  Менеджер по работе
                group_work = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Продажи / Менеджер по работе с партнерами')])
                users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_work)], order='id')
                if data.manager_work_id.id == uid or uid in users_work:
                    access += 'w'

                #  Руководитель по развитию
                group_upwork = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Продажи / Руководитель по развитию партнеров')])
                users_upwork = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_upwork)], order='id')
                if uid in users_upwork:
                    access += 'h'

                #  Руководитель направления SEO
                group_coord = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Руководитель направления SEO')])
                users_coord = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_coord)], order='id')
                if uid in users_coord:
                    access += 's'

                #  Специалист направления SEO
                if data.respon_user_id.id == uid:
                    access += 'r'

                #  SEO оптимизатор
                if data.executive_user_id.id == uid:
                    access += 'o'

                res[data.id] = access
        return res

    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'create_date': fields.datetime('Дата создания', select=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', select=True),
        'site': fields.char('Сайт партнера', size=255),

        'manager_work_id': fields.many2one('res.users', 'Менеджер по работе с партнерами', select=True),
        'manager_upwork_id': fields.related('partner_id', 'user_id', type="many2one", relation="res.users", string="Менеджер по развитию партнеров", store=False, readonly=True),

        'respon_user_id': fields.many2one(
            'res.users',
            'Ответственный',
            select=True,
            domain="[('groups_id','in',[79])]"),
        'executive_user_id': fields.many2one(
            'res.users',
            'Исполнитель',
            select=True,
            domain="[('groups_id','in',[106])]"),

        # вкладка "данные по стратегии"
        'servis_ids': fields.many2many(
            'brief.services.stage',
            'brief_services_stage_seo_strategys_rel',
            'seo_id',
            'b_ser_id',
            string='Услуги',
            select=True),
        'promotion_word': fields.boolean('Продвижение по словам'),
        'promotion_trafic': fields.boolean('Продвижение по трафику'),
        'seo_audit': fields.boolean('SEO аудит'),
        'seo_optim': fields.boolean('SEO оптимизация'),
        'promotion_other': fields.boolean('Другой вариант'),
        'cont_file_name': fields.char('Договор', size=255),
        'cont_file': fields.binary('Договор'),
        'deal_date': fields.date('Дата подписания договора', select=True),
        'strategy_id': fields.one2many('seo.strategys.stage', 'seo_strategys_id', 'Стратегия'),
        'strategy_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Стратегия',
            domain=[('res_model', '=', 'seo.strategys'), ('tmp_res_model', '=', 'strategy')],
            context={'res_model': 'seo.strategys'}
        ),
        'reason_stop_work': fields.text('Причина остановки работ'),

        #  вкладка "Данные по оплатам"
        'payment_id': fields.one2many('seo.strategys.payments.stage', 'seo_strategys_id', 'Оплаты'),
        'debt': fields.function(
            _get_debt,
            type='float',
            method=True,
            store=False,
            string='Итого долг'),

        #  вкладка "Реализация стратегии"
        #  показатели SLA SMM
        'indicators': fields.one2many('seo.indicators.stage', 'seo_strategys_id', 'Показатели SLA SEO'),
        #  итого по каждому отчетному периоду
        'total_sla_ids': fields.one2many('seo.sla.total', 'seo_strategys_id', 'Итого по каждому отчетному периоду'),
        'reports_monthly': fields.one2many('seo.reports_monthly.stage', 'seo_strategys_id', 'Ежемесячные отчеты'),
        'reports_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Ежемесячные отчеты',
            domain=[('res_model', '=', 'seo.strategys'), ('tmp_res_model', '=', 'report')],
            context={'res_model': 'seo.strategys'}
        ),

        # футер
        'comment': fields.text('Комментарий по доработке'),
        'state': fields.selection(zip(state_first.keys(), state_first.values()), 'статус', readonly=True),

        # Дедлайн для выполнения заданий
        'deadline': fields.datetime('Дедлайн на следующее состояние', readonly=True),

        'history_ids': fields.one2many('seo.history', 'seo_id', 'История'),
        'message_ids': fields.one2many('seo.messages', 'seo_id', 'Переписка по проекту'),
        'contract_ids': fields.one2many('seo.contract', 'seo_id', 'Договор'),
        'contracts_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Договор',
            domain=[('res_model', '=', 'seo.strategys'), ('tmp_res_model', '=', 'contract')],
            context={'res_model': 'seo.strategys'}
        ),

        'task_ids': fields.one2many('seo.strategy.tasks', 'seo_id', 'Задачи в рамках проекта'),

        #'usr_permission': fields.function(_check_p, method=True, string=u"Права", type="char"),
        'check_w': fields.function(_check_access, method=True, string="Менеджер по работе", type="boolean", invisible=True),
        'check_h': fields.function(_check_access, method=True, string="Руководитель по развитию", type="boolean", invisible=True),
        'check_s': fields.function(_check_access, method=True, string="Руководитель направления SEO", type="boolean", invisible=True),
        'check_r': fields.function(_check_access, method=True, string="Специалист направления SEO", type="boolean", invisible=True),
        'check_o': fields.function(_check_access, method=True, string="SEO оптимизатор", type="boolean", invisible=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'state': 'draft',
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        field = self.browse(cr, uid, ids[0])
        next_state = values.get('state', False)
        state = field.state

        error = ''
        if next_state and next_state != state:

            #  draft -> approval_approval_application_start
            if state == 'draft' and next_state == 'approval_application_start':
                if not values.get('servis_ids', False) and not field.servis_ids:
                    error += ' Необходимо создать запись(и) услуг;'

                if not field.contracts_ids and not values.get('contracts_ids', False):
                    error += ' Необходимо прикрепить файл договора;'

                if not field.promotion_word and not field.promotion_trafic and not field.promotion_other \
                   and not field.seo_optim and not field.seo_audit \
                   and not values.get('promotion_word', False) and not values.get('promotion_trafic', False) \
                   and not values.get('promotion_other', False) and not values.get('seo_optim', False) \
                   and not values.get('seo_audit', False):
                    error += ' Необходимо отметить тип продвижения;'

            #  approval_application_start -> appointment_responsible
            if state == 'approval_application_start' and next_state == 'appointment_responsible':
                if not field.payment_id:
                    error += ' Необходимо создать запись(и) оплат;'

            #  appointment_responsible -> preparation_strategy
            if state == 'appointment_responsible' and next_state == 'preparation_strategy':
                if not field.respon_user_id and not values.get('respon_user_id', False):
                    error += 'Необходимо выбрать ответственного; '

            #  preparation_strategy -> adoption_strategy
            if state == 'preparation_strategy' and next_state == 'adoption_strategy':
                if not field.strategy_ids:
                    error += ' Необходимо создать запись(и) стратегии;'
                if not field.reports_ids:
                    error += ' Необходимо создать запись(и) ежемесячных отчетов'

            #  adoption_strategy -> completion_strategy
            if state == 'adoption_strategy' and next_state == 'completion_strategy':
                if not values.get('comment', False) and not field.comment:
                    error += 'Необходимо ввести комментарий по доработке'

            #  completion_strategy -> adoption_strategy
            if state == 'completion_strategy' and next_state == 'adoption_strategy':
                pass

            #  adoption_strategy -> appointment_executive
            if state == 'adoption_strategy' and next_state == 'appointment_executive':
                pass

            #  appointment_executive -> implementation_strategy
            if state == 'appointment_executive' and next_state == 'implementation_strategy':
                if not field.respon_user_id and not values.get('respon_user_id', False):
                    error += 'Необходимо выбрать исполнителя'

            #  implementation_strategy -> strategy_analysis
            if state == 'implementation_strategy' and next_state == 'strategy_analysis':
                if not field.indicators:
                    error += 'Необходимо создать запись(и) показателей'

            #  strategy_analysis -> preparation_strategy
            if state == 'strategy_analysis' and next_state == 'preparation_strategy':
                pass

            #  strategy_analysis -> implementation_strategy
            if state == 'strategy_analysis' and next_state == 'implementation_strategy':
                pass

            #  implementation_strategy -> closed && strategy_analysis -> closed
            if state in ('implementation_strategy', 'strategy_analysis') and next_state == 'closed':
                if not field.reason_stop_work:
                    error += 'Необходимо ввести причину остановки компании'

        if error:
            raise osv.except_osv("SEO strategy", error)

        if next_state and next_state != state:
            values.update({'history_ids': [(0, 0, {
                'usr_id': uid,
                'state': self.state_first[next_state],
                'state_id': next_state
            })]})

        for attachment in values.get('strategy_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'seo.strategys'
                attachment[2]['tmp_res_model'] = 'strategy'
        for attachment in values.get('reports_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'seo.strategys'
                attachment[2]['tmp_res_model'] = 'report'
        for attachment in values.get('contracts_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'seo.strategys'
                attachment[2]['tmp_res_model'] = 'contract'

        return super(seo_strategys, self).write(cr, uid, ids, values, context)

seo_strategys()


class seo_strategys_stage(osv.osv):
    _name = "seo.strategys.stage"
    _description = u"Процесс SEO - Справочник Стратегий"

    # ToDo: DELETE

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    _columns = {
        'create_date': fields.datetime('Дата записи'),
        'strat_file_name': fields.char('Стратегия', size=255),
        'strat_file': fields.binary('Стратегия (файл)'),
        'user_id': fields.many2one('res.users', 'Автор записи', readonly=True),
        'seo_strategys_id': fields.many2one('seo.strategys', 'SEO', invisible=True),

    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
seo_strategys_stage()


class seo_strategys_payments_stage(osv.osv):
    _name = "seo.strategys.payments.stage"
    _description = u"Процесс SEO -Справочник Оплаты"

    def _get_debt_pay(self, cr, uid, ids, field_name, arg, context):
        result = {}
        obj = self.browse(cr, uid, ids[0], context=context)
        result[obj.id] = obj.sum_plane - obj.sum_fackt
        return result

    _columns = {
        'pay_date_plane': fields.datetime('Дата плановая'),
        'sum_plane': fields.float('Сумма планируемая $'),
        'pay_date_fackt': fields.datetime('Дата фактическая'),
        'sum_fackt': fields.float('Сумма фактическая $'),
        'debt_pay': fields.function(_get_debt_pay,
                                    type='float',
                                    method=True,
                                    store=True,
                                    string='Долг'),
        'seo_strategys_id': fields.many2one('seo.strategys', 'SEO', invisible=True),

    }

seo_strategys_payments_stage()


class seo_indicators_stage(osv.osv):
    _name = "seo.indicators.stage"
    _description = u"Процесс SEO - Справочник Показатели"

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
            raise osv.except_osv("Ошибка вычислений!", u"Вы пытаетесь делить на 0! Измените плановые показатели.")

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
        TotalObj = self.pool.get('seo.sla.total')
        Tid = TotalObj.search(cr, uid, [('date_id.id', '=', row.date_id.id), ('seo_strategys_id', '=', row.seo_strategys_id.id)], limit=1)
        if not Tid:
            values = {
                'influence': row.influence,
                'mbo': compliance * row.influence,
                'date_id': row.date_id.id,
                'seo_strategys_id': row.seo_strategys_id.id,
            }
            TotalObj.create(cr, uid, values, context)
        else:
            Rid = self.search(cr, uid, [('date_id.id', '=', row.date_id.id), ('seo_strategys_id', '=', row.seo_strategys_id.id)])
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
                'seo_strategys_id': row.seo_strategys_id.id,
            }
            TotalObj.write(cr, uid, Tid, values, context)
        return res

    _columns = {
        'date_id': fields.many2one('sla.interval.date', 'Период', required=True, select=True),
        'sla_id': fields.many2one('indicators.sla.stage', 'Показатели', required=True),
        'influence': fields.float('Вес', required=True),
        'plan': fields.float('План', required=True),
        'fact': fields.float('Факт'),
        'compliance': fields.function(
            _compliance_indic_mdo,
            type='float',
            method=True,
            store=True,
            string='Выполнение',
            multi='compliance'
        ),
        'mbo': fields.function(
            _compliance_indic_mdo,
            type='float',
            method=True,
            store=True,
            string='MBO',
            multi='mbo'),
        'seo_strategys_id': fields.many2one('seo.strategys', 'SEO стратегия', invisible=True),
    }

    def unlink(self, cr, uid, ids, context=None):
        Rrows = self.browse(cr, uid, ids[0], context)
        TotalObj = self.pool.get('seo.sla.total')
        Tid = TotalObj.search(cr, uid, [('date_id.id', '=', Rrows.date_id.id), ('seo_strategys_id', '=', Rrows.seo_strategys_id.id)])
        Rids = self.search(cr, uid, [('date_id.id', '=', Rrows.date_id.id), ('seo_strategys_id', '=', Rrows.seo_strategys_id.id)])
        if len(Rids) > 1:
            Tdata = TotalObj.browse(cr, uid, Tid[0], context)
            values = {
                'influence': Tdata.influence - Rrows.influence,
                'mbo': Tdata.mbo - Rrows.mbo,
            }
            TotalObj.write(cr, uid, Tid, values, context)
        else:
            TotalObj.unlink(cr, uid, Tid, context)
        return super(seo_indicators_stage, self).unlink(cr, uid, ids[0], context)

seo_indicators_stage()


class seo_sla_total(osv.osv):
    _name = "seo.sla.total"
    _description = u"Процесс SEO - Итого SLA показателей"
    _order = "create_date desc"

    _columns = {
        'date_id': fields.many2one('sla.interval.date', 'Период', readonly=True, select=True),
        'influence': fields.float('Вес', readonly=True),
        'mbo': fields.float('MBO', readonly=True),
        'seo_strategys_id': fields.many2one('seo.strategys', 'SEO стратегия', invisible=True),
    }

seo_sla_total()


class seo_reports_monthly_stage(osv.osv):
    _name = "seo.reports_monthly.stage"
    _description = u"Процесс SEO - Справочник Отчеты"
    # ToDo: DELETE

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        print field_name
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    _columns = {
        'create_date': fields.datetime('Дата записи', readonly=True),
        'rep_file_name': fields.char('Отчет (имя)', size=255),
        'rep_file': fields.binary('Отчет (файл)'),
        'user_id': fields.many2one('res.users', 'Автор записи', readonly=True),
        'seo_strategys_id': fields.many2one('seo.strategys', 'SEO', invisible=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

seo_reports_monthly_stage()


class seo_history(osv.osv):
    _name = 'seo.history'
    _description = u'Процесс SEO - История переходов'
    _columns = {
        'usr_id': fields.many2one('res.users', 'Перевел'),
        'create_date': fields.datetime('Дата создания'),
        'state': fields.char('На этап', size=65),
        'state_id': fields.char('Этап', size=65),
        'seo_id': fields.many2one('seo.strategys', 'SEO', invisible=True),
    }

    _order = "create_date desc"

seo_history()


class seo_messages(osv.osv):
    _name = 'seo.messages'
    _description = u'Процесс SEO - Сообщения'

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
        'seo_id': fields.many2one('seo.strategys', 'SEO', invisible=True),
    }

    _rec_name = 'cr_date'

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'cr_date': fields.datetime.now()
    }

    _order = "create_date desc"

seo_messages()


class seo_contract(osv.osv):
    _name = 'seo.contract'
    _rec_name = 'create_date'

    # ToDo: DELETE

    _columns = {
        'create_date': fields.datetime('Дата записи', readonly=True),
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'rep_file_id': fields.many2one('attach.files', 'Договор'),
        'seo_id': fields.many2one('seo.strategys', 'SEO', invisible=True),
    }

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        #'cr_date': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

seo_contract()


class seo_strategy_tasks(osv.osv):
    _name = "seo.strategy.tasks"
    _description = u"Процесс SEO - Справочник Задачи в рамках проекта"

    _columns = {
        'name': fields.char('Задача', size=256),
        'user_id': fields.many2one('res.users', 'Автор записи', readonly=True),
        'date_complete': fields.datetime('Дата выполнения'),
        'seo_id': fields.many2one('seo.strategys', 'SEO', invisible=True),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

seo_strategy_tasks()
