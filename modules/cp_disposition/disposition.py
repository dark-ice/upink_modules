# coding=utf-8
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model

LINES = (
    ('commercial', 'Коммерческие вопросы'),
    ('partner', 'Обслуживание партнеров'),
    ('infra', 'Инфраструктура и кадры'),
)


class CpDisposition(Model):
    _name = 'cp.disposition'
    _description = u'Распоряжения'

    _columns = {
        'user_id': fields.many2one('res.users', 'Автор'),
        'create_date': fields.datetime('Дата распоряжения', readonly=True,),
        'line': fields.selection(LINES, 'Направленость', required=True),
        'from_date': fields.date('С какого числа, месяца, года'),
        'on_date': fields.date('На какое число, месяц, год '),
        'not_later_date': fields.date('Не позднее какой даты?'),
        'to_date': fields.date('По какое число, месяц, год'),
        'financier_id': fields.many2one('res.users', 'Фин. контролер'),
        'period_id': fields.many2one('kpi.period', 'За какой месяц, год', domain=[('calendar', '=', 'rus')]),
        'seeing': fields.text('Причина (в связи с)'),
        'working_off': fields.boolean('без/с отработкой'),
        'working_dates': fields.one2many('cp.disposition.workingoff', 'disposition_id', 'Даты отработки'),
        'working_off_days': fields.integer('С отработкой', help='Кол-во дней'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник'),
        'job_id': fields.many2one('hr.job', 'Должность'),
        'department_id': fields.many2one('hr.department', 'Направление'),

        'trip': fields.text('Цель командировки'),
        'trip_place': fields.text('Место командировки'),

        'grade_id': fields.many2one('kpi.grade', 'Грейд, категория'),
        'reason': fields.text('Основание'),
        'remark': fields.text('Замечание, выговор, применить удержание'),
        'direction_name': fields.char('Название направления', size=256),
        'at_rate': fields.float('В размере'),
        'date_ot': fields.date('От какой даты'),
        'next_attestation': fields.date('Дата следующей аттестации'),
        'motive_rewarding': fields.text('Мотив награждения'),
        'promotion_type': fields.text('Вид поощрения', help='Объявить благодарность, наградить ценным подарком или почетной грамотой, выдать премию и др'),
        'teacher_id': fields.many2one('hr.employee', 'Наставник'),
        'financing_source': fields.char('Источник финансирования', size=256),
        'commission_ids': fields.many2many('res.users', 'Комиссия в составе'),
        'term': fields.integer('В какой срок', help='Кол-во дней'),
        'amount': fields.float('Сумма удержания'),
        'statement_date': fields.date('Заявление от'),
        'instate_date': fields.date('Дата принятия'),

        'comments': fields.text('Комментарии'),

        'salary': fields.float('Оклад'),
        'variable': fields.float('Переменная часть'),

        'post_probation_grade_id': fields.many2one('kpi.grade', 'Грейд, категория после испыт. срока'),
        'probation_grade_id': fields.many2one('kpi.grade', 'Грейд, категория на испыт. сроке'),
        'duration_probation': fields.integer('Длительность испытательного срока'),

        #'': fields.many2many('res.users', 'Кто согласовывает'),
        #'': fields.many2many('res.users', 'Для кого опубликовать'),
    }

    _defaults = {
        'user_id': lambda s, cr, u, cntx: u,
    }


CpDisposition()


class CpDispositionCategory(Model):
    _name = 'cp.disposition.category'
    _description = u'Распоряжения - Категории'

    _columns = {
        'line': fields.selection(LINES, 'Направленость', required=True),
        'name': fields.char('Название', size=256),
        'template_id': fields.many2one('ir.attachment', 'Файл шаблона договора'),
    }

CpDispositionCategory()


class CpDispositionWorkingOff(Model):
    _name = 'cp.disposition.workingoff'
    _description = u'Распоряжения - Отпработки'
    _rec_name = 'date'

    _columns = {
        'disposition_id': fields.many2one('cp.disposition', 'Распоряжение'),
        'date': fields.date('Дата'),
    }
CpDispositionWorkingOff()