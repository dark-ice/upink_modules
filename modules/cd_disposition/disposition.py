# coding=utf-8
from lxml import etree
from openerp import tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model
import simplejson

LINES = (
    ('commercial', 'Коммерческие вопросы'),
    ('partner', 'Обслуживание партнеров'),
    ('infra', 'Инфраструктура и кадры'),
)


class CdDisposition(Model):
    _name = 'cd.disposition'
    _description = u'Распоряжения'

    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(r['id'], tools.ustr('Распоряжение № {id} от {date}'.format(id=r['id'], date=r['disposition_date']) )) for r in
                self.read(cr, user, ids, ['disposition_date'], context, load='_classic_write')]

    def check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for record in self.read(cr, uid, ids, ['user_id'], context):
            res[record['id']] = {
                'check_a': True,
                'check_f': True,
            }

        return res

    _columns = {
        'user_id': fields.many2one('res.users', 'Автор', readonly=True,),
        'disposition_date': fields.date('Дата распоряжения', readonly=True,),
        'line': fields.selection(LINES, 'Направленость', required=True,),
        'category_id': fields.many2one('cd.disposition.category', 'Категория', domain="[('line', '=', line)]", required=True,),

        'from_date': fields.date('С какого числа, месяца, года'),
        'on_date': fields.date('На какое число, месяц, год '),
        'from_date_second': fields.date('С какого числа, месяца, года', help='20 месяца'),
        'on_date_second': fields.date('На какое число, месяц, год '),
        'not_later_date': fields.date('Не позднее какой даты?'),
        'not_later_date_second': fields.date('Уведомить не позже'),
        'to_date': fields.date('По какое число, месяц, год'),
        'financier_id': fields.many2one('res.users', 'Фин. контролер'),
        'period_id': fields.many2one('kpi.period', 'За какой месяц, год', domain=[('calendar', '=', 'rus')]),
        'seeing': fields.text('Причина (в связи с)'),

        'working_off': fields.boolean('без/с отработкой'),
        'working_dates': fields.one2many('cd.disposition.workingoff', 'disposition_id', 'Даты отработки'),
        'working_off_days': fields.integer('С отработкой', help='Кол-во дней'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник'),
        'job_id': fields.many2one('hr.job', 'Должность'),
        'next_job_id': fields.many2one('hr.job', 'Новая должность'),
        'department_id': fields.many2one('hr.department', 'Направление'),
        'next_department_id': fields.many2one('hr.department', 'Новое направление'),

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
        'commission_ids': fields.many2many(
            'res.users',
            'disposition_users_rel',
            'disposition_id',
            'user_id',
            string='Комиссия в составе'),
        'term': fields.integer('В какой срок', help='Кол-во дней'),
        'amount': fields.float('Сумма удержания'),
        'statement_date': fields.date('Заявление от'),
        'instate_date': fields.date('Дата принятия'),

        'comments': fields.text('Комментарии'),

        'salary': fields.float('Оклад'),
        'salary_per': fields.float('%'),
        'variable': fields.float('Переменная часть'),
        'variable_per': fields.float('%'),

        'post_probation_grade_id': fields.many2one('kpi.grade', 'Грейд, категория после испыт. срока'),
        'probation_grade_id': fields.many2one('kpi.grade', 'Грейд, категория на испыт. сроке'),
        'duration_probation': fields.integer('Длительность испытательного срока'),

        'year': fields.char('Год', size=4),
        'no_work': fields.text('Нерабочие праздничные дни'),
        'work_day': fields.text('Перенести'),

        #'': fields.many2many('res.users', 'Кто согласовывает'),
        #'': fields.many2many('res.users', 'Для кого опубликовать'),


        'check_f': fields.function(
            check_access,
            method=True,
            string="Проверка на все согласовано",
            type="boolean",
            invisible=True,
            multi='check',
        ),
        'check_a': fields.function(
            check_access,
            method=True,
            string="Проверка на автора",
            type="boolean",
            invisible=True,
            multi='check',
        ),
    }

    _defaults = {
        'user_id': lambda s, cr, u, cntx: u,
        'disposition_date': lambda *a: fields.date.today(),
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(CdDisposition, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            cr.execute('SELECT f.name, array_agg(disposition_category_id) FROM disposition_category_fields_relation r LEFT JOIN ir_model_fields f on (f.id=r.field_id) GROUP BY f.name')
            for field, categories in cr.fetchall():
                for node in doc.xpath("//field[@name='{0}']".format(field,)):
                    invisible = [['category_id', 'not in', categories]]
                    modifiers = simplejson.loads(node.get('modifiers')) or {}
                    if modifiers.get('invisible'):
                        modifiers['invisible'] += invisible
                    else:
                        modifiers['invisible'] = invisible
                    node.set('modifiers', simplejson.dumps(modifiers))
            result['arch'] = etree.tostring(doc)
        return result


CdDisposition()


class CdDispositionCategory(Model):
    _name = 'cd.disposition.category'
    _description = u'Распоряжения - Категории'

    _columns = {
        'line': fields.selection(LINES, 'Направленость', required=True),
        'name': fields.char('Название', size=256),
        'template_id': fields.many2one('ir.attachment', 'Файл шаблона договора'),
        'field_ids': fields.many2many(
            'ir.model.fields',
            'disposition_category_fields_relation',
            'disposition_category_id',
            'field_id',
            'Доступные поля',
            domain=['&', ('model_id', '=', 'cd.disposition'), '!', ('name', 'ilike', 'check')]),
    }

CdDispositionCategory()


class CdDispositionWorkingOff(Model):
    _name = 'cd.disposition.workingoff'
    _description = u'Распоряжения - Отпработки'
    _rec_name = 'date'

    _columns = {
        'disposition_id': fields.many2one('cd.disposition', 'Распоряжение'),
        'date': fields.date('Дата'),
    }
CdDispositionWorkingOff()