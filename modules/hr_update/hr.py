# -*- coding: utf-8 -*-
from openerp.osv import fields
from openerp.osv.orm import Model


class hr_employee(Model):
    _name = "hr.employee"
    _inherit = "hr.employee"
    _log_create = True

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.browse(cr, uid, ids, context):
            if uid == 1:
                res[data.id] = {
                    'check_e': True,
                    'check_l': True,
                    'check_t': True,
                    'check_s': True,
                    'check_h': True,
                }
            else:
                res[data.id] = {
                    'check_e': False,
                    'check_l': False,
                    'check_t': False,
                    'check_s': False,
                    'check_h': False,
                }
                top_users = self.pool.get('res.users').search(cr, 1, [('groups_id', '=', 37)])

                #  Сотрудник
                if data.user_id.id == uid:
                    res[data.id]['check_e'] = True

                #  Руководитель + топы
                if (data.parent_id and data.parent_id.user_id.id == uid) or uid in top_users:
                    res[data.id]['check_l'] = True

                #  Топы
                if uid in top_users:
                    res[data.id]['check_t'] = True

                #  Сис админы
                if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', 'in', [193, 194])]):
                    res[data.id]['check_s'] = True

                #  Hr
                if uid in self.pool.get('res.users').search(cr, 1, [('groups_id', '=', 14)]):
                    res[data.id]['check_h'] = True
        return res

    _columns = {
        'manager': fields.boolean("Является руководителем?"),
        'work_skype': fields.char("Рабочий skype", size=250),
        'attachment_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Вложения',
            domain=[('res_model', '=', 'hr.employee')],
            context={'res_model': 'hr.employee'}
        ),
        'instate_date': fields.date('Дата приема в штат'),
        'language_ids': fields.one2many(
            'hr.employee.language',
            'employee_id',
            'Знание языков',
        ),
        'university_id': fields.many2one('hr.university', 'ВУЗ'),
        'specialty': fields.char('Специальность', size=250),

        'children': fields.integer('Количество детей '),
        'babies_ids': fields.one2many(
            'hr.employee.babies',
            'employee_id',
            'Дети',
        ),
        'category': fields.selection(
            (
                ('top', 'ТОП-менеджер'),
                ('head', 'Линейный руководитель'),
                ('leading', 'Ведущий специалист'),
                ('specialist', 'Специалист'),
                ('on probation', 'Сотрудник на испытательном сроке'),
            ), 'Категория'
        ),
        'history_job_ids': fields.one2many(
            'res.history',
            'res_id',
            'История должностей',
            domain=[('res_model', '=', 'employee.job.history')],
            readonly=True
        ),
        'certification_ids': fields.one2many(
            'hr.employee.certifications',
            'employee_id',
            'Аттестации',
        ),
        'address_residence_id': fields.many2one('res.partner.address', 'Адрес фактического проживания'),
        'vehicle': fields.char('Личный транспорт', size=64),
        'account_number': fields.char('Номер карточного счета', size=250),
        'training_ids': fields.one2many(
            'hr.employee.external.training',
            'employee_id',
            'Участие во внешнем обучении',
        ),

        'kpi_ids': fields.one2many(
            'kpi.kpi',
            'employee_id',
            'KPI',
        ),
        'expert_assessment_ids': fields.one2many(
            'kpi.expert.assesment',
            'employee_id',
            'Экспертные оценки',
            domain=[('state', '=', 'work')]
        ),

        'account_id': fields.many2one('account.account', 'ФЛП/ООО', domain=[('type', '!=', 'closed')]),

        'access_ids': fields.one2many(
            'hr.employee.access',
            'employee_id',
            'Доступы'
        ),
        'inn': fields.char("ИНН", size=10),

        'check_l': fields.function(
            _check_access,
            method=True,
            string="Проверка на линейного руководителя",
            type="boolean",
            invisible=True,
            multi='access'
        ),
        'check_t': fields.function(
            _check_access,
            method=True,
            string="Проверка на топ менеджеров + Зоя",
            type="boolean",
            invisible=True,
            multi='access'
        ),
        'check_e': fields.function(
            _check_access,
            method=True,
            string="Проверка на сотрудника",
            type="boolean",
            invisible=True,
            multi='access'
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string="Проверка на сис админов",
            type="boolean",
            invisible=True,
            multi='access'
        ),
        'check_h': fields.function(
            _check_access,
            method=True,
            string="Проверка на hr",
            type="boolean",
            invisible=True,
            multi='access'
        ),


    }
    
    _defaults = {
        'check_t': lambda s, c, u, cnt: True,
        'check_l': lambda s, c, u, cnt: True,
    }

    def get_user(self, cr, user, ids, context=None):
        if isinstance(ids, (tuple, list)):
            employee_id = ids[0]
        else:
            employee_id = ids
        data = self.browse(cr, user, employee_id, context)
        if data.user_id:
            return data.user_id
        else:
            return False

    def get_employee(self, cr, user, ids, context=None):
        if isinstance(ids, (tuple, list)):
            user_id = ids[0]
        else:
            user_id = ids

        employee_ids = self.search(cr, user, [('user_id', '=', user_id)])
        if employee_ids:
            return self.browse(cr, user, employee_ids[0], context)
        else:
            return False

    def get_department_manager(self, cr, user, ids, context=None):
        if isinstance(ids, (tuple, list)):
            employee_id = ids[0]
        else:
            employee_id = ids
        employee = self.browse(cr, user, employee_id, context)
        if employee.manager:
            return employee
        elif employee.department_id:
            return employee.department_id.manager_id
        else:
            return False

    def write(self, cr, user, ids, vals, context=None):
        for attachment in vals.get('attachment_ids', []):
            if attachment[0] == 0:
                attachment[2]['res_model'] = 'hr.employee'

        for record in self.read(cr, user, ids, ['job_id']):
            if vals.get('job_id') and vals['job_id'] != record['job_id'] and record['job_id']:
                vals.update({'history_job_ids': [(0, 0, {
                    'res_model': 'employee.job.history',
                    'name': self.pool.get('hr.job').read(cr, user, vals['job_id'], ['name'])['name'],
                    'prev_value': record['job_id'][1],
                })]})

        return super(hr_employee, self).write(cr, user, ids, vals, context)

hr_employee()


class HrUniversity(Model):
    _name = 'hr.university'
    _description = u'Сотрудники - ВУЗ'

    _columns = {
        'name': fields.char('ВУЗ', size=250),
    }
HrUniversity()


class HrLanguage(Model):
    _name = 'hr.language'
    _description = u'Сотрудники - Иностранные языки'

    _columns = {
        'name': fields.char('Иностранный язык', size=250),
    }
HrLanguage()


class HrEmployeeLanguage(Model):
    _name = 'hr.employee.language'
    _description = u'Сотрудники - Знание языков'

    _columns = {
        'name': fields.many2one('hr.language', 'Язык'),
        'value': fields.selection(
            (
                (1, "Начальный"),
                (2, "Базовый"),
                (3, "Средний"),
                (4, "Выше среднего"),
                (5, "Свободное владение"),
            ), 'Уровень владения'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', invisible=True),
    }
HrEmployeeLanguage()


class HrEmployeeBabies(Model):
    _name = 'hr.employee.babies'
    _description = u'Сотрудники - Дети'

    _columns = {
        'name': fields.date('Дата рождения'),
        'gender': fields.selection([('male', 'Мальчик'), ('female', 'Девочка')], 'Пол'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', invisible=True),
    }
HrEmployeeBabies()


class History(Model):
    _name = "res.history"
    _description = u'История изменений'

    _columns = {
        'name': fields.char('Новое значение', size=250),
        'prev_value': fields.char('Предыдущие значение', size=250),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'create_eid': fields.many2one('hr.employee', 'Сотрудник'),
        'res_model': fields.char('Модель', size=250),
        'res_id': fields.integer('ID записи'),
    }

    _defaults = {
        'create_eid': lambda s, c, u, cnt: s.pool.get('hr.employee').get_employee(c, u, u).id,
    }
History()


class HrEmployeeCertifications(Model):
    _name = 'hr.employee.certifications'
    _description = u'Сотрудники - Аттестации'

    _columns = {
        'name': fields.selection(
            [
                ('-2', '-2'),
                ('-1', '-1'),
                ('0', '0'),
                ('+1', '+1'),
                ('+2', '+2')
            ], 'Результаты аттестации', required=True),
        'state': fields.selection(
            (
                ('new_job', 'Перевод на другую должность'),
                ('new_division', 'Перевод в другое направление'),
            ), 'Действие'
        ),
        'certification_date': fields.date('Дата аттестации'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', invisible=True),
    }

    _defaults = {
        'name': '0',
    }
HrEmployeeCertifications()


class HrEmployeeExternalTraining(Model):
    _name = 'hr.employee.external.training'
    _description = u'Сотрудники - Цчастие во внешнем обучении'

    _columns = {
        'name': fields.char('Что', size=250),
        'when': fields.datetime('Когда'),
        'where': fields.char('Где', size=250),
        'how_much': fields.char('Стоимость', size=250),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', invisible=True),
    }
HrEmployeeExternalTraining()


class HrEmployeeAccess(Model):
    _name = 'hr.employee.access'
    _description = u'Сотрудники - Цчастие во внешнем обучении'

    _columns = {
        'name': fields.selection(
            (
                ('skype', 'Skype'),
                ('email', 'Эл. почта'),
                ('erp', 'ERP'),
                ('soft', 'Soft'),
                ('icq', 'ICQ'),
            ), 'Тип доступа', required=True
        ),
        'login': fields.char('Логин', size=250),
        'password': fields.char('Пароль', size=250),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник', invisible=True),
    }
HrEmployeeAccess()