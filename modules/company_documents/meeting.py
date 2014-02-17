# coding=utf-8
__author__ = 'skripnik'
from openerp.osv import fields
from openerp.osv.orm import Model


class UserMeeting(Model):
    _name = 'user.meeting'

    def get_job_for_initiator(self, cr, uid, context):
        if uid:
            job = "Не найден"
            employee_pool = self.pool.get('hr.employee')
            employee_ids = employee_pool.search(cr, uid, [('user_id', '=', uid)])
            job_id = employee_pool.read(cr, uid, employee_ids[0], ['job_id'])
            if job_id['job_id']:
                job = job_id['job_id'][1]
            return job

    _columns = {

        'initiator_id': fields.many2one('res.users', 'Инициатор'),
        'job_char': fields.char('Должность', size=128),
        'create_date': fields.date('Дата создания'),
        'from_time': fields.datetime('С', required=True),
        'to_time': fields.datetime('По', required=True),
        'name': fields.char('Тема', size=256, required=True),
        'comment': fields.text('Комментарий'),
        'participants_ids': fields.one2many(
            'meeting.participants',
            'meeting_id',
            string='Участники',
        ),
        'questions_ids': fields.one2many(
            'meeting.questions',
            'meeting_id',
            string='Вопросы',
        )
    }

    _defaults = {
        'initiator_id': lambda s, cr, u, cntx: u,
        'job_char': lambda s, cr, u, cntx: UserMeeting.get_job_for_initiator(s, cr, u, cntx),
    }

UserMeeting()


class MeetingQuestions(Model):
    _name = 'meeting.questions'

    _columns = {
        'meeting_id': fields.many2one('user.meeting', 'Номер совещяния', invisible=False),
        'initiator_id': fields.many2one('res.users', 'Автор', readonly=True),
        'name': fields.text('Содержание'),
        'answer_text': fields.text('Решение'),
        'time_left': fields.datetime('Время решения до'),
        'responsible_id': fields.many2one('res.users', 'Ответственный'),
    }

    _defaults = {
        'initiator_id': lambda s, cr, u, cntx: u,
    }

MeetingQuestions()


class MeetingParticipants(Model):
    _name = 'meeting.participants'

    def get_job(self, cr, uid, ids, user_id, context=None):
        if user_id:
            job = "Не найден"
            employee_pool = self.pool.get('hr.employee')
            employee_ids = employee_pool.search(cr, uid, [('user_id', '=', user_id)])
            job_id = employee_pool.read(cr, uid, employee_ids[0], ['job_id'])
            if job_id['job_id'][1]:
                job = job_id['job_id'][1]
            return {'value': {'job_char': job}}

    _columns = {
        'user_id': fields.many2one(
            'res.users',
            'Пользователь',
            readonly=False,
            help='Заполняется автоматически'),
        'meeting_id': fields.many2one('user.meeting', 'Распоряжение', invisible=True),
        'job_char': fields.char(string='Должность', size=256),
        'label': fields.boolean('Присутствие'),
        'comm': fields.text('Комментарий')
    }

MeetingParticipants()