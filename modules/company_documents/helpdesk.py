# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, timedelta
from openerp.osv import fields
from openerp.osv.orm import Model
from openerp import netsvc
from notify import notify

wf_service = netsvc.LocalService("workflow")
__author__ = 'Andrey Karbanovich'


class act_window(Model):
    _inherit = "ir.actions.act_window"
    _columns = {
        'domain': fields.text('Domain Value', help="Optional domain filtering of the destination data, as a Python expression"),
    }


class HelpdeskCategoryStage(Model):
    _name = "helpd.category.stage"
    _description = u"Служебные документы: Категории HelpDesk"

    _columns = {
        'name': fields.char('Категория', size=250),
        'user_res_id': fields.many2one('hr.employee', 'Ответственный'),
    }

HelpdeskCategoryStage()


class HelpDesk(Model):
    _name = 'help.desk'
    _description = u'Служебные документы: HelpDesk'
    _order = "create_date desc"

    states = (
        ('draft', 'Черновик'),
        ('waiting', 'На согласовании'),
        ('rework', 'На доработке'),
        ('decision', 'Принятие решения'),
        ('redecision', 'На доработке(принятие решения)'),
        ('closed', 'Закрыто принимающим решение'),
        ('inwork', 'Исполнение'),
        ('approval', 'Сдано на утверждение'),
        ('failed', 'Не выполнено'),
        ('init_accepted', 'Принято инициатором'),
        ('init_failed', 'Не принято инициатором'),
        ('cancel', 'Отменено'),

    )

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        if ids:
            data_ids = self.browse(cr, uid, ids, context)
            employee_pool = self.pool.get('hr.employee')
            for data in data_ids:
                access = str()

                #  Автор
                if data.author and data.author.user_id.id == uid:
                    access += 'a'

                #  Руководитель автора
                if data.author and employee_pool.get_department_manager(cr, uid, data.author.id).id == uid:
                    access += 'd'

                #  Автор == Руководителю
                if data.author and data.department_manager and data.author == data.department_manager:
                    access += 'e'

                #  Кому
                if data.send_to and (data.send_to.user_id.id == uid or employee_pool.get_department_manager(cr, uid, data.send_to.id).id == uid):
                    access += 's'

                #  Руководитель кому
                if data.send_to and employee_pool.get_department_manager(cr, uid, data.send_to.id).id == uid:
                    access += 'm'

                #  Ответственный
                if data.responsible_employee and (data.responsible_employee.user_id.id == uid or employee_pool.get_department_manager(cr, uid, data.responsible_employee.id).id == uid):
                    access += 'r'

                #  Руководитель ответственного
                if data.responsible_employee and employee_pool.get_department_manager(cr, uid, data.responsible_employee.id).id == uid:
                    access += 'h'

                val = False

                letter = name[6]

                if letter in access:
                    val = True
                res[data.id] = val
        return res

    def _check_manager(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for record in self.browse(cr, uid, ids, context):
            if 'department' in name and record.author:
                employee = record.author
            elif 'send' in name and record.send_to:
                employee = record.send_to
            elif 'responsible' in name and record.responsible_manager:
                employee = record.responsible_employee
            else:
                employee = None

            if employee:
                res[record.id] = self.pool.get('hr.employee').get_department_manager(cr, uid, employee.id).id
            else:
                res[record.id] = None
        return res

    def check_deadline(self, cr, uid, context=None):
        return True

    def get_department_manager(self, cr, uid, ids):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        if ids:
            return self.set_manager_fields(cr, uid, ids, 'author', 0, ids)

    def onchange_categories(self, cr, uid, ids, field_name, context=None):
        res = {}
        employee_pool = self.pool.get('hr.employee')
        if field_name:
            send_to = self.pool.get('helpd.category.stage').browse(cr, uid, field_name).user_res_id.id
            send_manager = employee_pool.get_department_manager(cr, uid, send_to).id
            res['send_to'] = send_to
            res['send_manager'] = send_manager
            if send_to == employee_pool.get_employee(cr, uid, uid):
                res['check_s'] = True
            else:
                res['check_s'] = False

            if send_manager == employee_pool.get_employee(cr, uid, uid):
                res['check_m'] = True
            else:
                res['check_m'] = False
        return {'value': res}

    def set_manager_fields(self, cr, uid, ids, field, empl_id, usr_id=None):
        res = {}
        employee_pool = self.pool.get('hr.employee')
        cur_empl = employee_pool.get_employee(cr, uid, uid).id
        if usr_id:
            empl_id = employee_pool.get_employee(cr, uid, usr_id).id

        if empl_id:
            manager = employee_pool.get_department_manager(cr, uid, empl_id).id
        else:
            manager = None

        if manager == cur_empl:
            check_m = True
        else:
            check_m = False

        if empl_id == cur_empl:
            check_e = True
        else:
            check_e = False

        if field == 'author':
            manager_field = 'department_manager'
            check_m_field = 'check_d'
            check_e_field = 'check_a'
        elif field == 'send_to':
            manager_field = 'send_manager'
            check_m_field = 'check_m'
            check_e_field = 'check_s'
        else:
            manager_field = 'responsible_manager'
            check_m_field = 'check_h'
            check_e_field = 'check_r'

        res[manager_field] = manager
        res[check_m_field] = check_m
        res[check_e_field] = check_e
        return res

    def onchange_manager(self, cr, uid, ids, empl, field='author', context=None):
        res = {}
        if empl:
            res = self.set_manager_fields(cr, uid, ids, field, empl)
        return {'value': res}

    _columns = {
        'id': fields.integer("ID", size=11, select=True, help='Назначение: показывает порядковый номер заявки. \nДанное поле заполняется автоматически на этапе создания новой заявки. \nРедактировать это поле нельзя.'),
        'create_date': fields.datetime('Дата создания', readonly=True, help='Назначение: отображает дату создания заявки. \nДанное поле заполняется автоматически на этапе создания новой заявки. \nРедактировать это поле нельзя.'),
        'admin_group': fields.many2one('res.groups', 'Админ', readonly=True, invisible=True),

        'author': fields.many2one('hr.employee', 'От кого', readonly=True, help='Назначение: отображается автор созданной заявки. \nДанное поле заполняется автоматически на этапе создания новой заявки. \nРедактировать это поле нельзя.'),
        'department_manager': fields.many2one('hr.employee', 'Руководитель направления', readonly=True, help='Назначение: отображается руководитель автора заявки. \nДанное поле заполняется автоматически на этапе создания новой заявки. \nРедактировать это поле нельзя.'),
        'send_to': fields.many2one('hr.employee', 'Кому', help='Назначение: данное поле отображает получатся заявки. \nНа этапах "Черновик" и "На доработке" это поле обязательно к заполнению. \nНа остальных этапах это поле менять или редактировать нельзя. \nПоле заполняется автоматически при выборе определенной категории заявки.'),
        'send_manager': fields.many2one('hr.employee', 'Руководитель кому', readonly=True, help=''),
        'responsible_employee': fields.many2one('hr.employee', 'Ответственный за исполнение', help='Назначение: в данном поле отображается ответственное лицо за выполнение заявки. \nДанное поле не является обязательным к заполнению. \nНа этапе "Принятие решение" это поле можно редактировать. \nПоле заполняется выбором определенного сотрудника из ниспадающего списка.'),
        'responsible_manager': fields.many2one('hr.employee', 'Руководитель ответственного', readonly=True, help=''),

        'name': fields.char('Тема', size=255, required=True, help='Назначение: в данном поле отображается тема заявки. \nТип: текстовое поле для ввода данных. \nНа этапах "Черновик" и "На доработке" это поле обязательно к заполнению. \nНа остальных этапах это поле менять или редактировать нельзя.'),
        'categories_id': fields.many2one('helpd.category.stage', 'Категория', required=True, help='Назначение: данное поле отображает категорию созданной заявки. \nНа этапах "Черновик" и "На доработке" это поле обязательно к заполнению. \nНа остальных этапах это поле менять или редактировать нельзя. \nПоле заполняется выбором нужного варианта из ниспадающего списка.'),

        'content': fields.text('Содержание', help='Назначение: в данном поле отображается максимально полное содержание заявки. \nТип: текстовое поле для ввода данных. \nНа этапах "Черновик" и "На доработке" это поле обязательно к заполнению. \nНа остальных этапах это поле менять или редактировать нельзя.'),
        'fio': fields.char('ФИО', size=250, help=''),
        'department_id': fields.many2one('hr.department', 'Направление', help=''),
        'job_id': fields.many2one('hr.job', 'Должность', help=''),
        'date_of_birth': fields.date('Число\месяц\год рождения', help=''),
        'technique': fields.text('Тип техники', help=''),
        'soft': fields.text('Необходимое ПО', help=''),
        'accounts': fields.text('Какие аккаунты необходимы:Эл почта, Skype', help=''),
        'extension': fields.selection(
            [
                ('no', 'Нет'),
                ('yes', 'Да'),
            ], 'Необходим внутренний номер', help=''),
        'number': fields.char('Номер', size=250, help=''),
        'call_direction': fields.selection(
            [
                ('ukraine', 'Украина'),
                ('russia', 'Россия'),
                ('es', 'ЕС'),
            ], 'Направление звонков', help=''),

        'decision': fields.char('Принято решение', size=255, help='Назначение: в данном поле отображается принятое решение относительно определенной заявки. \nТип: текстовое поле для ввода данных, необязательно к заполнению. \nНа этапе "Принятие решения" это поле можно редактировать. \nНа остальных этапах это поле менять или редактировать нельзя.'),
        'accepted': fields.selection([('no', 'Нет'), ('yes', 'Да')], 'Принято к исполнению', help=''),

        'deadline': fields.datetime('Срок исполнения', required=True, help='Назначение: в данном поле отображается deadline выполнения заявки. \nНа этапах "Черновик", "На согласовании" и "На доработке" это поле обязательно к заполнению. \nНа остальных этапах это поле менять или редактировать нельзя. Поле заполняется выбором определенной даты из календаря.'),
        'completed': fields.selection([('no', 'Нет'), ('yes', 'Да')], 'Отметка об исполнении', help=''),

        'comments': fields.text('Комментарии', help='Назначение: указывается комментарий принимающего решение по текущей заявке. Тип: текстовое поле для ввода данных. На этапе "Принятие решения" это поле можно редактировать. На остальных этапах это поле менять или редактировать нельзя.'),
        'redo_comment': fields.text('Комментарий по доработке', help='Назначение: указывается комментарий по доработке текущей заявки. Тип: текстовое поле для ввода данных. На этапах "На согласовании" (если заявка отправляется на доработку) - это поле обязательно к заполнению. На остальных этапах это поле менять или редактировать нельзя.'),
        'init_comment': fields.text('Комментарий инициатора', help='Назначение: указывается комментарий автора заявки. Тип: текстовое поле для ввода данных. На этапе "Сдано на утверждение" это поле можно редактировать. На остальных этапах это поле менять или редактировать нельзя.'),
        'resp_comment': fields.text('Комментарий овтетственного', help='Назначение: указывается комментарий исполнителя по текущей заявке. Тип: текстовое поле для ввода данных. На этапе "Исполнение" это поле можно редактировать. На остальных этапах это поле менять или редактировать нельзя.'),

        'state': fields.selection(states, 'Этап', readonly=True, help=''),
        'history_ids': fields.one2many('helpdesk.history', 'hd_id', 'История переходов', help='Назначение: отображается история переходов по определенной заявке. Это поле заполняется автоматически. Менять или редактировать его нельзя.'),

        #  Права
        'check_a': fields.function(
            _check_access,
            method=True,
            string="Проверка на автора",
            type="boolean",
            invisible=True
        ),
        'check_d': fields.function(
            _check_access,
            method=True,
            string="Проверка на руководителя автора",
            type="boolean",
            invisible=True
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string="Проверка на кому",
            type="boolean",
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string="Проверка на руководителя кому",
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
        'check_h': fields.function(
            _check_access,
            method=True,
            string="Проверка на руководителя ответственного",
            type="boolean",
            invisible=True
        ),
        'check_e': fields.function(
            _check_access,
            method=True,
            string="Проверка на совпадения автора и руководителя",
            type="boolean",
            invisible=True
        ),
        'put_in_time': fields.boolean('Сдано не в срок'),
    }

    _defaults = {
        'state': 'draft',
        'author': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).id,
        'department_manager': lambda s, c, u, cnt: s.get_department_manager(c, u, u)['department_manager'],
        'extension': 'no',
        'check_a': True,
        'check_d': lambda s, c, u, cnt: s.get_department_manager(c, u, u)['check_d'],
        'admin_group': 2,
    }

    def _check_redo_comment(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], ['state', 'redo_comment'], context)
        if data.get('state') == 'rework' and not data.get('redo_comment'):
            return False
        return True

    def _check_inwork(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], ['state', 'responsible_employee', 'decision'], context)
        if data.get('state') == 'inwork' and not data.get('responsible_employee') and not data.get('decision'):
            return False
        return True

    def _check_comments(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], ['state', 'comments'], context)
        if data.get('state') == 'closed' and not data.get('comments'):
            return False
        return True

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        record = self.browse(cr, uid, ids, context)[0]
        employee_pool = self.pool.get('hr.employee')
        next_state = values.get('state', False)
        state = record.state

        category = values['categories_id'] if values.get('categories_id', False) else record.categories_id
        if isinstance(category, (int, long)):
            category = self.pool.get('helpd.category.stage').browse(cr, uid, category)
        values['send_to'] = category.user_res_id.id

        if values.get('send_to', False) or record.send_to:
            send_to = values['send_to'] if values.get('send_to', False) else record.send_to.id
            values['send_manager'] = employee_pool.get_department_manager(cr, uid, send_to).id

        if values.get('responsible_employee', False) or record.responsible_employee:
            responsible_employee = values['responsible_employee'] if values.get('responsible_employee', False) else record.responsible_employee.id
            values['responsible_manager'] = employee_pool.get_department_manager(cr, uid, responsible_employee).id

        if next_state and next_state != state:
            if state == 'draft':
                #if
                pass
            if state == 'inwork' and next_state == 'approval':
                if datetime.now(pytz.utc) > datetime.strptime(record.deadline, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc):
                    values['put_in_time'] = True
                else:
                    values['put_in_time'] = False

            values.update({'history_ids': [(0, 0, {
                'usr_id': self.pool.get('hr.employee').get_employee(cr, uid, uid).id,
                'state': self.get_state(next_state)[1]
            })]})

        return super(HelpDesk, self).write(cr, uid, ids, values, context)

    def automatic_setter(self, cr, uid, state='waiting'):
        if state == 'waiting':
            td = timedelta(days=1)
            signal = 'act_w_c'
        else:
            td = timedelta(days=7)
            signal = 'act_app_ia'

        deadline_time = datetime.now(pytz.utc) - td
        records = self.search(cr, uid, [('state', '=', state)])
        history_pool = self.pool.get('helpdesk.history')
        #   ('create_date', '<', deadline_time.strftime('%Y-%m-%d %H:%M:%S'))
        for record in self.browse(cr, uid, records):
            domain = [
                ('hd_id', '=', record.id),
            ]

            history_id = history_pool.search(
                cr,
                uid,
                domain,
                limit=1,
                order='create_date desc')
            if history_id:
                history = history_pool.browse(cr, uid, history_id[0])
                create_date = datetime.strptime(history.create_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
                if create_date < deadline_time:
                    wf_service.trg_validate(uid, self._name, record.id, signal, cr)

    def workflow_setter(self, cr, user, ids, state='draft'):
        return self.write(cr, user, ids, {'state': state})

    def get_state(self, state):
        return [item for item in self.states if item[0] == state][0]

    def _check_deadline(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context)
        if data.create_date > data.deadline and data.state != 'init_accepted':
            return False
        return True

    _constraints = [
        #(_check_redo_comment,
        # 'Заполните поле комментарий',
        # [u'Комментарий на доработку']),
        (_check_inwork,
         'Вы не заполнили поле сотрудник или решение по исполнению',
         [u'Ответственный сотрудник', u'Решение']),
        (_check_comments,
         'При закрытии записки, обязательно, укажите причину в комментариях',
         [u'Комментарии']),
        (_check_deadline,
         'Дата выполнения не может быть раньше даты создания заявки',
         [u'Срок исполнения']),
    ]

HelpDesk()


class HelpdeskHistory(Model):
    _name = 'helpdesk.history'
    _description = u'HelpDesk - История переходов'
    _log_create = True
    _order = "create_date desc"
    _rec_name = 'state'

    _columns = {
        'usr_id': fields.many2one('hr.employee', 'Перевел'),
        'state': fields.char('На этап', size=65),
        'create_date': fields.datetime('Дата', readonly=True),
        'hd_id': fields.many2one('help.desk', 'HelpDesk', invisible=True),
    }

    _defaults = {
        'usr_id': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).id,
    }

HelpdeskHistory()
