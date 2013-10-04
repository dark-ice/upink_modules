# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime, timedelta

from osv import fields, osv
from crm import crm
from openerp import tools
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


AVAILABLE_STATES = [
            ('draft', 'Черновик'),
            ('agreement', 'Согласование'),
            ('approval', 'Утверждение'),
            ('appointment', 'Назначение ответственного'),
            ('adoption_in_work', 'Принятие в работу'),
            ('in_the_work', 'В работу'),
            ('closed', 'Вакансия закрыта'),
            ('completion_agr', 'На доработку(Согласование)'),
            ('completion_app', 'На доработку(Утверждение)'),
            ('completion_adop', 'На доработку(Принятие в работу)'),
            ('cancel', 'Отменена')
]
STATES_LIST = {
            'draft' : u'Черновик',
            'agreement' : u'Согласование',
            'approval' : u'Утверждение',
            'appointment' : u'Назначение ответственного',
            'adoption_in_work' : u'Принятие в работу',
            'in_the_work' : u'В работу',
            'closed' : u'Вакансия закрыта',
            'completion_agr' : u'На доработку(Согласование)',
            'completion_app' : u'На доработку(Утверждение)',
            'completion_adop' : u'На доработку(Принятие в работу)',
            'cancel' : u'Отменена',
}

#~ class hr_employee(osv.osv):
    #~ _name = 'hr.employee'
    #~ _inherit = 'hr.employee'
    #~ 
    #~ def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=None):
        #~ new_args = ['|',('active','=',True),('active','=',False)]
        #~ args += new_args
        #~ return super(osv.osv, self).search(cr, uid, args, offset, limit, order, context, order)
#~ 
#~ hr_employee()

class hr_vacancy_stage(osv.osv):
    _name = "hr.vacancy.stage"
    _description = "Справочник причин возникновения вакансий"
    _order = 'id desc'
    _columns = {
        'name': fields.char('Причины возникновения вакансии', size=125, select=True),
    }
hr_vacancy_stage()

class hr_vacancy_control(osv.osv):
    
    _name = "hr.vacancy.control"
    _columns = {
        'state' : fields.selection(AVAILABLE_STATES, 'Этап', required=True),
        'time_type': fields.selection([('minutes','Минуты'),('hours','Часы'),('days','Дни')],'Тип времени'),
        'time' : fields.integer('Время перехода'),
        'message' : fields.text('Сообщение', required=True, help="Доступные поля для замены ДОЛЖНОСТЬ, АВТОР, ЭТАП, ДАТА СОЗДАНИЯ.\n Поля которые необходимо заменить пишите большими буквами"),
        'send_to': fields.selection([('director','Ответственный директор'),('manager','Руководитель отдела'),('users','Выбрать пользователей')], 'Отправить', required=True),
        'users' : fields.many2many('res.users','hr_control_users_send_to','hr_control_id','user_id', string="Выберите пользователей"),
    }
    
    _defaults = {
        'time_type' : 'hours',
        'send_to' : 'director',
    }
    
    def _check_state_uniqueness(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            unique_id = self.search(cr,uid,[('state','=',field.state)])
            if unique_id != ids:
                return False
        return True
    
    _constraints = [
        (_check_state_uniqueness,
        'Запись для такого утверждения уже есть, если хотите изменить время - отредактируйте её.',
        ['state']),
    ]
    
hr_vacancy_control()

class hr_vacancy(crm.crm_case, osv.osv):
    
    _name = "hr.vacancy"
    _description = "Заявка на вакансию"
    _order = 'create_date'
    
    def send_request(self, cr, uid, ids):
       obj_r = self.pool.get('res.request')
       data = self.browse(cr, uid, ids[0])
       for field in self.browse(cr, uid, ids):
           depart = self.pool.get('hr.department').read(cr, uid, int(field.department_id), ['name'], context=None)
           job = self.pool.get('hr.job').read(cr, uid, int(field.job_id), ['name'], context=None)
           usercr = self.pool.get('res.users').read(cr, uid, int(field.user_id), ['name'], context=None)
           datecr = unicode(field.create_date, "utf-8")
           statebp =  field.state
           userid = int(field.user_id)
           resuserid = int(field.responsible_user)
           textmessg = unicode("Заявка на вакансию на должность «%s» в подразделение «%s», созданная %s автором %s переведена на этап «%s».", "utf-8")
       volies = {
                'body' :  textmessg % (unicode(job['name']),unicode(depart['name']),datecr,unicode(usercr['name']),STATES_LIST[field.state]),
                'name' : unicode("Заявка на вакансию", "utf-8"),
                'state' : 'waiting',
                'priority' : '1',
                'act_from' : uid,
                'active' : True,
                'act_to' : 0,
       }
       if statebp in ['agreement', 'approval', 'appointment']:
            group_id = False
            if statebp in ['agreement', 'appointment']:
               group_id = self.pool.get('res.groups').search(cr, uid, [('name','=','Human Resources / HrSupervisor')])
            if statebp == 'approval':
               user_ids = [data.department_id.responsible_directors.id]
            if group_id:
               user_ids = self.pool.get('res.users').search(cr, uid, [('groups_id','in',group_id)])
            if user_ids:
                for u in user_ids:
                    if u != 1:
                        volies['act_to'] = u
                        obj_r.create(cr, uid, volies)
            elif statebp not in ['draft', 'cancel']:
                if statebp == 'adoption_in_work' and resuserid:
                   volies['act_to'] = resuserid
                   obj_r.create(cr, uid, volies)
                elif userid:
                     volies['act_to'] = userid
                     obj_r.create(cr, uid, volies)
       return False
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = {'accept_user': False, 
                    'valid_user': False, 
                    'state': 'draft', 
                    'applicant_user': False,
                    'responsible_user': False,
                    'vacancy_enddate': False,
                    'state_cooment': False}
        return super(osv.osv, self).copy(cr, uid, id, default, context)
    
    def vacancy_deadline(self, cr, uid, context=None):
        request = self.pool.get('res.request')
        control = self.pool.get('hr.vacancy.control')
        control_ids = control.search(cr,uid,[('time','!=',0)])
        for control_id in control_ids:
            control_data = control.browse(cr, uid, control_id)
            vacancy_ids = self.search(cr, uid, [('state', '=', control_data.state)])
            for item in vacancy_ids:
                data = self.browse(cr, uid, item)
                # create date is used when control date is not defined
                # timedelta is a difference between current_date and date of state have been changed
                if not data.control_date: 
                    create_date = datetime.strptime(data.create_date, '%Y-%m-%d %H:%M:%S')
                else:
                    create_date = datetime.strptime(data.control_date, '%Y-%m-%d %H:%M:%S')
                current_date = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
                timedelta = current_date - create_date
                # preparing timedelta with custom time type
                if control_data.time_type == 'hours':
                    deadline_time = datetime.timedelta(hours=control_data.time)
                elif control_data.time_type == 'minutes':
                    deadline_time = datetime.timedelta(minutes=control_data.time)
                elif control_data.time_type == 'days':
                    deadline_time = datetime.timedelta(days=control_data.time)
                # deadline timedelta is ready
                if timedelta > deadline_time:
                    # preparing message text
                    message_text = control_data.message
                    replace_dict = [(u"ДОЛЖНОСТЬ", data.job_id.name),
                                    (u"АВТОР", data.user_id.name),
                                    (u"ЭТАП", STATES_LIST[control_data.state]),
                                    (u"ДАТА СОЗДАНИЯ",data.create_date)]
                    for item in replace_dict:
                        message_text = message_text.replace(item[0],item[1])
                    # message text is ready
                    # preparing act_to users
                    users = []
                    if control_data.send_to == 'director':
                        users.append(data.department_id.responsible_directors.id)
                    elif control_data.send_to == 'manager':
                        users.append(data.department_id.manager_id.user_id.id)
                    elif control_data.send_to == 'users':
                        for user in control_data.users:
                            users.append(user.id)
                    # users is ready
                    message = {
                        'body' :  message_text,
                        'name' : unicode("Необработанная заявка", "utf-8"),
                        'state' : 'waiting',
                        'priority' : '1',
                        'act_from' : uid,
                        'active': True,
                        'act_to': False,
                        }
                    for user in users:
                        message['act_to'] = user
                        request_id = request.search(cr,uid,['&',('body','=',message['body']),('act_to','=',message['act_to'])])
                        if not request_id:
                            request.create(cr, uid, message)
        return False
    
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор заявки', select=True),
        'create_date': fields.datetime('Дата', readonly=True, select=True),
        'control_date': fields.datetime('Контрольная Дата'),
        'department_id': fields.many2one('hr.department', 'Подразделение', help='Выберите подразделение, в которое требуется сотрудник'),
        'job_id':fields.many2one('hr.job', 'Должность', select=True, help='Укажите вакантную должность'),
        'valid_user':fields.many2one('res.users', 'Согласовал пользователь'),
        'accept_user':fields.many2one('res.users', 'Утвердил пользователь'),
        'responsible_user':fields.many2one('res.users', 'Ответственный за выполнение', select=True),
        'applicant_user':fields.many2one('hr.applicant','Соискатель'),
        # First group
        'causes':fields.many2one('hr.vacancy.stage','Причины возникновения вакансии', help='Укажите причину, например «расширение штата»'),
        'funct_pos':fields.text('Функциональные обязанности', help='Перечислите все основные функциональные обязанности, которые будут у сотрудника'),
        'numbers':fields.integer("Количество человек в подчинении", help='Укажите в цифрах'),
        'perspekt_up':fields.char('Перспективы карьерного роста', size=255),
        'state':fields.selection(AVAILABLE_STATES, "Статус заявки"),
         'state_coment':fields.text('Комментарий на доработку'),
        # Second group
        'education':fields.selection([
            ('it_does_not_matter', 'не имеет значения'),
            ('higher', 'высшее'),
            ('incomplete_higher', 'неполное высшее'),
            ('secondary_special', 'среднее специальное'),
            ('average','среднее'),
            ('student', 'учащийся'),
        ], "Образование"),
        'pre_education':fields.text('Примечание к образованию', help='При необходимости указывается профиль образования или другие дополнительные требования'),
        'experience':fields.selection([
            ('no_experience', 'нет опыта'),
            ('lover1y', 'менее 1 года'),
            ('1to3y', '1-3 года'),
            ('3to6y', '3-6 лет'),
            ('upto6y','более 6 лет'),
        ], "Опыт работы"),
        'pre_experience':fields.text('Примечание к опыту работы', help='При необходимости указывается конкретная сфера деятельности, в которой нужен опыт или другие дополнительные требования'),
         # year old
        'in_y':fields.integer("от"),
        'to_y':fields.integer("до"),
        'sex':fields.selection([
            ('male', 'мужской'),
            ('female', 'женский'),
            ('1to3y', 'не имеет значения'),
        ], "Пол"),
         # lengiges
        'a_lang':fields.text('a)' , help='Например: английский – со словарем'),
        'b_lang':fields.text('b)', help='Например: английский – со словарем'),
        'pc_knowledge':fields.selection([
            ('pc_user', 'пользователь'),
            ('pc_pruser', 'уверенный пользователь'),
            ('pc_hruser', 'продвинутый пользователь'),
            ('pc_programer', 'программист'),
        ], "Знание компьютера"),
        'pre_pc_knowledge':fields.text('Примечание'),
        'regime_emp':fields.selection([
            ('full_reg', 'полный день'),
            ('half_reg', 'неполный день'),
            ('free_reg', 'удаленная работа'),
        ], "Режим работы"),
        'form_recruit':fields.selection([
            ('permanent_job', 'постоянная работа'),
            ('project_work', 'проектная работа'),
        ], "Форма найма"),
        # ZP )))
        'zp_trial_period':fields.integer("На время испытательного срока"),
        'zp_aftrial_period':fields.integer("После испытательного срока"),
        'long_trial_period':fields.selection([
            ('1manf', '1 месяц'),
            ('2manf', '2 месяца'),
            ('3manf', '3 месяца'),
        ], "Длительность испытательного срока"),
        'trips':fields.boolean("Наличие командировок"),
        'dop_zp':fields.char('Дополнительные выплаты', size=255),
        'social_package':fields.char('Социальный пакет', size=255),
        'vacancy_enddate':fields.datetime('Срок выполнения заявки', select=True),
        'vacancy_coments':fields.text('Дополнительная информация', help='Здесь Вы можете указать все те требования, которые не вошли в предыдущие поля'),
    }
    _defaults = {
        'user_id':  lambda self, cr, uid, context: uid,
        'state': lambda *a: 'draft',
    }
    def onchange_department(self, cr, uid, ids, job_id, context = None):
        result = {}
        if job_id:
            job_data = self.pool.get('hr.job').browse(cr,uid,job_id,context=context)
            result['department_id'] = job_data.department_id.id
        return {'value': result}
        
    def _check_state_coment(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            if field.state_coment == False and field.state in ['completion_adop', 'completion_app', 'completion_agr']:
                return False
        return True
        
    def _check_responsible_user(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            if (not field.responsible_user or not field.vacancy_enddate) and field.state in ['adoption_in_work']:
                return False
        return True
        
    def _check_end_workflow(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            if not field.applicant_user and field.state in ['closed']:
                return False
        return True
        
    def _check_start_end_data(self, cr, uid, ids):
         for field in self.browse(cr, uid, ids):
             date_end = False
             date_create = False
             if field.vacancy_enddate:
                date_end = datetime.strptime(field.vacancy_enddate, "%Y-%m-%d %H:%M:%S")
             if field.create_date:
                date_create = datetime.strptime(field.create_date, "%Y-%m-%d %H:%M:%S")
             if date_create and date_end:
                if date_create > date_end and field.state in ['adoption_in_work']:
                   return False
         return True

    _constraints = [
        (_check_state_coment,
        'Необходимо отредактировать коментарий к требуемым изменениям',
        ['state_coment', 'state']),
        (_check_start_end_data,
        'Срок выполнения заявки позже чем дата создания',
        ['vacancy_enddate', 'state', 'create_date']),
        (_check_responsible_user,
        'Необходимо ввести поле "Ответственный за выполнение" "Срок выполнения заявки"',
        ['responsible_user', 'state', 'vacancy_enddate']),
        (_check_end_workflow,
        'Необходимо ввести поле "Соискатель"',
        ['applicant_user', 'state']),
        ]
    _order = 'id desc'


    def action_canceled(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'cancel', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        return True

    def action_agreement(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'agreement', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_approval(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            if field.state in ['agreement']:
               self.write(cr, uid, ids, { 'valid_user': uid })
        self.write(cr, uid, ids, { 'state': 'approval', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_appointment(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'appointment', 'accept_user': uid, 'control_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        self.send_request(cr, uid, ids)
        return True

    def action_adoption_of_the_work(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'adoption_in_work', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_in_the_work(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'in_the_work', 'state_coment': '', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_for_completion_agr(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'completion_agr', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_for_completion_app(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'completion_app', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_for_completion_adop(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'completion_adop', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_closed(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'closed', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        self.send_request(cr, uid, ids)
        return True

    def action_draft(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'draft', 'control_date': time.strftime('%Y-%m-%d %H:%M:%S') })
        return True
        
hr_vacancy()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
