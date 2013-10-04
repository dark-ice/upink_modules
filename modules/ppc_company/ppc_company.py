# -*- encoding: utf-8 -*-
from osv import fields, osv
from datetime import datetime
from notify import notify
from openerp import tools
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


class ppc_reklam_stage(osv.osv):
    _name = "ppc.reklam.stage"
    _description = u"PPC рекламная система - справочник"
    _columns = {
        'name': fields.char('Название', size=165, required=True),
    }

ppc_reklam_stage()


class ppc_company(osv.osv):
    _name = "ppc.company"
    _description = u"Запуск и реализация кампании PPC "
    _order = "create_date desc"
    _table = "ppc_company"
    _rec_name = "site"

    workflow_name = 'ppc.company.ppc_company_wrk'
    _msg_fields = ['id', 'user_id', 'partner_id', 'site']

    # zipом в _columns
    state_first = {
        'draft': 'черновик',
        'approval_application': 'согласование заявки',
        'appointment_account_manager': 'назначение аккаунт менеджера',
        'preparation_startup_company': 'подготовка запуска кампании',
        'completion_company': 'доработка кампании',
        'adoption_company': 'утверждение кампании',
        'implementation_company': 'реализация кампании',
        'closed': 'кампания остановлена',
    }

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
        data = self.browse(cr, uid, ids[0])
        values = result = {'state': state}

        self.write(cr, uid, ids, values)

        if state in ('preparation_startup_company', 'completion_company', 'implementation_company'):
            result['users'] = [data.acc_manager_id.id]
        elif state in ('appointment_account_manager', 'adoption_company'):
            group = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'PPC/Координатор')])
            result['users'] = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group)], order='id')
        elif state == 'approval_application':
            group = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Продажи / Руководитель по развитию партнеров')])
            result['users'] = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group)], order='id')
        else:
            result['users'] = []

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

                #  Автор
                if data.user_id.id == uid and data.state == 'draft':
                    access += 'u'

                #  Менеджеры 2 и 3
                group_work = self.pool.get('res.groups').search(cr, 1, [('name', 'in', ('Продажи / Менеджер по работе с партнерами', 'Продажи / Менеджер по развитию партнеров', 'Продажи / Руководитель по развитию партнеров', 'Продажи / Руководитель по работе с партнерами'))])
                users_work = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_work)], order='id')
                if data.manager_work_id.id == uid or uid in users_work:
                    access += 'w'

                #  Руководители по развитию определяют ответственного
                group_upwork = self.pool.get('res.groups').search(cr, 1, [('name', 'ilike', 'Продажи / Руководитель по развитию партнеров')])
                users_upwork = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_upwork)], order='id')
                if uid in users_upwork:
                    access += 'h'

                #  PPC/Координатор
                group_coord = self.pool.get('res.groups').search(cr, 1, [('id', 'in', (92, 108))])
                users_coord = self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', group_coord)], order='id')
                if uid in users_coord:
                    access += 'c'

                #  Аккаунт менеджер
                if data.acc_manager_id.id == uid:
                    access += 'a'

                res[data.id] = access
        return res

    def default_department_manager(self, cr, uid, context=None):
        employee_id = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        data = self.pool.get('hr.employee').browse(cr, uid, employee_id[0])
        if data.manager:
            return employee_id[0]
        if data.department_id:
            return data.department_id.manager_id.id
        return False

    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор заявки', select=True),
        'create_date': fields.datetime('Дата создания', select=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', select=True, domain="[('partner_type','in', ('upsale', ' ', '', False))]"),
        'reklam_id': fields.many2one('ppc.reklam.stage', 'Рекламная система', select=True),
        'site': fields.char('Сайт партнера', size=255),
        'manager_work_id': fields.many2one('res.users', 'Менеджер по работе с партнерами', select=True),
        'manager_upwork_id': fields.related('partner_id', 'user_id', type="many2one", relation="res.users", string="Менеджер по развитию партнеров", store=False, readonly=True),

        # вкладка "данные по оплатам"
        'payments': fields.one2many('ppc.payments.stage', 'ppc_company_id', 'Оплаты'),
        # вкладка "данные по кампании"
        'acc_manager_id': fields.many2one(
            'res.users',
            'Аккаунт менеджер',
            select=True,
            domain="[('groups_id','in',[107])]"
        ),
        'access': fields.one2many('ppc.access.stage', 'ppc_company_id', 'Доступы'),
        'additional_data_company': fields.text('Дополнительные данные по кампании'),
        'reason_stop_company': fields.text('Причина остановки кампании'),
        # вкладка "Реализация кампании"
        # показатели SLA проекта
        'indicators': fields.one2many('ppc.indicators.stage', 'ppc_company_id', 'Показатели SLA PPC'),
        # итого по каждому отчетному периоду
        'total_sla_ids': fields.one2many('ppc.sla.total', 'ppc_company_id', 'Итого по каждому отчетному периоду'),
        'reports': fields.one2many('ppc.reports.stage', 'ppc_company_id', 'Отчеты'),

        'comment': fields.text('Комментарий по доработке'),
        'state': fields.selection([
            ('draft', 'черновик'),
            ('approval_application', 'согласование заявки'),
            ('appointment_account_manager', 'назначение аккаунт менеджера'),
            ('preparation_startup_company', 'подготовка запуска кампании'),
            ('completion_company', 'доработка кампании'),
            ('adoption_company', 'утверждение кампании'),
            ('implementation_company', 'реализация кампании'),
            ('closed', 'кампания остановлена'),
        ], 'статус', readonly=True),

        # Дедлайн для выполнения заданий
        'deadline': fields.datetime('Дедлайн на следующее состояние', readonly=True),

        'history_ids': fields.one2many('ppc.history', 'ppc_id', 'История'),
        'message_ids': fields.one2many('ppc.messages', 'ppc_id', 'Переписка по проекту'),
        'contract_ids': fields.one2many('ppc.contract', 'ppc_id', 'Договор'),

        'usr_permission': fields.function(_check_access, method=True, string=u"Права", type="char", invisible=True),
        #'department_manager': fields.many2one('hr.employee', u'Руководитель направления', invisible=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'state': 'draft',
        #'department_manager': lambda self, cr, uid, context: self.default_department_manager(cr, uid, context)
    }

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        field = self.browse(cr, uid, ids)[0]
        next_state = values.get('state', False)
        state = field.state

        if next_state and next_state != state:
            error = ''

            #  draft -> approval_application
            if state == 'draft' and next_state == 'approval_application':
                if not field.reports:
                    #error += "Необходимо прикрепить файл отчета;"
                    pass

                if not field.payments:
                    error += " Необходимо создать запись(и) оплаты"

            #  approval_application -> appointment_account_manager
            if state == 'approval_application' and state == 'appointment_account_manager':
                if not field.acc_manager_id and not values.get('acc_manager_id', False):
                    error += 'Необходимо выбрать аккаунт менеджера'

            #  appointment_account_manager -> preparation_startup_company
            if state == 'appointment_account_manager' and next_state == 'preparation_startup_company':
                pass

            #  preparation_startup_company -> adoption_company
            if state == 'preparation_startup_company' and next_state == 'adoption_company':
                if not field.access:
                    error += 'Необходимо создать запись(и) - доступы'

            #  adoption_company -> completion_company
            if state == 'adoption_company' and next_state == 'completion_company':
                if not values.get("comment", False) and not field.comment:
                    error += 'Необходимо ввести комментарий по доработке'

            #  completion_company -> preparation_startup_company
            if state == 'completion_company' and next_state == 'preparation_startup_company':
                pass

            #  adoption_company -> implementation_company
            if state == 'adoption_company' and next_state == 'implementation_company':
                pass

            #  implementation_company -> closed
            if state == 'implementation_company' and next_state == 'closed':
                if not field.reason_stop_company and not values.get('reason_stop_company', False):
                    error += 'Необходимо ввести причину остановки кампании'

            if error:
                raise osv.except_osv("PPC company", error)

            if next_state and next_state != state:
                values.update({'history_ids':
                                       [(0, 0, {
                                           'usr_id': uid,
                                           'state': self.state_first[next_state],
                                           'state_id': next_state
                                       })]})

        return super(ppc_company, self).write(cr, uid, ids, values, context)

ppc_company()


class ppc_payments_stage(osv.osv):
    _name = "ppc.payments.stage"
    _description = u"Справочник Оплаты"

    _columns = {
        'pay_detetime': fields.datetime('Дата оплаты'),
        'pay_currency': fields.many2one('partner.currency', 'Валюта оплаты'),
        'user_id': fields.many2one('res.users', 'Автор записи', readonly=True),
        'summ_pay': fields.float('Сумма оплаты'),
        'summ_pay_$': fields.float('Сумма оплаты в $'),
        'sum_enrollment_$': fields.float('Сумма к зачислению в $'),
        'ppc_company_id': fields.many2one('ppc.company', 'PPC', invisible=True),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

ppc_payments_stage()


class ppc_access_stage(osv.osv):
    _name = "ppc.access.stage"
    _description = u"Справочник Доступы"

    _columns = {
        'reklam_id': fields.many2one('ppc.reklam.stage', 'Рекламная система'),
        'login': fields.char('Логин', size=250),
        'password': fields.char('Пароль', size=64),
        'ppc_company_id': fields.many2one('ppc.company', 'PPC', invisible=True),
    }

ppc_access_stage()


class ppc_indicators_stage(osv.osv):
    _name = "ppc.indicators.stage"
    _description = u"Справочник Показатели PPC"
    _order = "date_id DESC"

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
            raise osv.except_osv(("Test"), (u"Вы пытаетесь делить на 0! Измените плановые показатели."))

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
        TotalObj = self.pool.get('ppc.sla.total')
        Tid = TotalObj.search(cr, uid,
            [('date_id.id', '=', row.date_id.id,), ('ppc_company_id', '=', row.ppc_company_id.id)], limit=1)
        if not Tid:
            values = {'influence': row.influence,
                      'mbo': compliance * row.influence,
                      'date_id': row.date_id.id,
                      'ppc_company_id': row.ppc_company_id.id,
            }
            TotalObj.create(cr, uid, values, context)
        else:
            Rid = self.search(cr, uid,
                [('date_id.id', '=', row.date_id.id), ('ppc_company_id', '=', row.ppc_company_id.id)])
            Rrows = self.browse(cr, uid, Rid, context)
            influence = 0
            mbo = 0
            for r in Rrows:
                influence = influence + r.influence
                if r.id == ids[0]:
                    mbo = mbo + mbo_row
                else:
                    mbo = mbo + r.mbo

            values = {'influence': influence,
                      'mbo': mbo,
                      'ppc_company_id': row.ppc_company_id.id,
            }
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
        'ppc_company_id': fields.many2one('ppc.company', 'PPC компания', invisible=True),
    }

    def unlink(self, cr, uid, ids, context=None):
        Rrows = self.browse(cr, uid, ids[0], context)
        TotalObj = self.pool.get('ppc.sla.total')
        Tid = TotalObj.search(cr, uid,
            [('date_id.id', '=', Rrows.date_id.id), ('ppc_company_id', '=', Rrows.ppc_company_id.id)])
        Rids = self.search(cr, uid,
            [('date_id.id', '=', Rrows.date_id.id), ('ppc_company_id', '=', Rrows.ppc_company_id.id)])
        if len(Rids) > 1:
            Tdata = TotalObj.browse(cr, uid, Tid[0], context)
            values = {'influence': Tdata.influence - Rrows.influence,
                      'mbo': Tdata.mbo - Rrows.mbo,
            }
            TotalObj.write(cr, uid, Tid, values, context)
        else:
            TotalObj.unlink(cr, uid, Tid, context)
        return super(ppc_indicators_stage, self).unlink(cr, uid, ids[0], context)

ppc_indicators_stage()


class ppc_sla_total(osv.osv):
    _name = "ppc.sla.total"
    _description = u"Итого SLA показателей PPC"

    _columns = {
        'date_id': fields.many2one('sla.interval.date', 'Период', readonly=True, select=True),
        'influence': fields.float('Вес', readonly=True),
        'mbo': fields.float('MBO', readonly=True),
        'ppc_company_id': fields.many2one('ppc.company', 'PPC компания', invisible=True),
    }

ppc_sla_total()


class ppc_reports_stage(osv.osv):
    _name = "ppc.reports.stage"
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
        'ppc_company_id': fields.many2one('ppc.company', 'PPC', invisible=True),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

ppc_reports_stage()


class ppc_enrollment_stage(osv.osv):
    _name = "ppc.enrollment.stage"
    _description = u"Справочник Отчеты"

    _columns = {
        'enrollment_date': fields.datetime('Дата зачисления'),
        'user_id': fields.many2one('res.users', 'Автор записи', readonly=True),
        'pay_currency': fields.many2one('partner.currency', 'Валюта оплаты'),
        'summ_enrollment': fields.float('Сумма зачисления (y.e. 1:30)'),
        'ppc_company_id': fields.many2one('ppc.company', 'PPC', invisible=True),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }

ppc_enrollment_stage()


class ppc_history(osv.osv):
    _name = 'ppc.history'
    _columns = {
        'usr_id': fields.many2one('res.users', 'Перевел'),
        'create_date': fields.datetime('Дата создания'),
        'state': fields.char('На этап', size=65),
        'state_id': fields.char('Этап', size=65),
        'ppc_id': fields.many2one('ppc.company', 'PPC company', invisible=True),
    }

    _order = "create_date desc"

ppc_history()


class ppc_messages(osv.osv):
    _name = 'ppc.messages'

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
        'ppc_id': fields.many2one('ppc.company', 'PPC company', invisible=True),
    }

    _rec_name = 'cr_date'

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'cr_date': datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

    _order = "cr_date desc"

ppc_messages()


class ppc_contract(osv.osv):
    _name = 'ppc.contract'
    _table = 'ppc_contract_new'

    _columns = {
        'name': fields.char('Название', size=100, invisible=True),
        'create_date': fields.datetime('Creation Date1', readonly=True),
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'rep_file_id': fields.many2one('attach.files', 'Договор'),
        'ppc_id': fields.many2one('ppc.company', 'PPC company', invisible=True),
    }

    _rec_name = 'create_date'

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'name': lambda *a: 'PPC contract'
    }

    _order = "create_date desc"

ppc_contract()
