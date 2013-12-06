# coding=utf-8
import datetime
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

STATE = (
    ('draft', 'Черновик'),
    ('agreement', 'На согласовании'),
    ('approval', 'На утверждении Ген. директором'),
    ('publish', 'Опубликовано'),
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

        'working_off_dates': fields.char('С отработкой', size=256, help='Дни для отработки'),
        'employee_id': fields.many2one('hr.employee', 'Сотрудник'),
        'job_id': fields.many2one('hr.job', 'Должность'),
        'next_job_id': fields.many2one('hr.job', 'Новая должность'),
        'teacher_job_id': fields.many2one('hr.job', 'Должность наставника'),
        'department_id': fields.many2one('hr.department', 'Направление'),
        'next_department_id': fields.many2one('hr.department', 'Новое направление'),
        'teacher_department_id': fields.many2one('hr.department', 'Направление наставника'),

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
        'term_str': fields.char('В какой срок', size=256, help='Прописью: в пятидневный срок с момента подписания распоряжения'),
        'amount': fields.float('Сумма удержания'),
        'statement_date': fields.date('Заявление от'),
        'instate_date': fields.date('Дата принятия'),

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

        'fio': fields.char('ФИО', size=256),

        'schedule_date': fields.date('Утвердить график'),
        'commission_date': fields.date('Создать аттестационную комиссию'),
        'set_date': fields.date('Передать', help='Бланки самооценки сотрудников и тестовые задания для сотрудников'),
        'list_date': fields.date('Подготовить и утвердить списки лиц'),
        'protocol_date': fields.date('Подготовить протоколы'),
        'top_date': fields.date('Передать генеральному директору'),
        'result_date': fields.date('Огласить результаты'),

        'agreement_user_ids': fields.many2many('res.users', 'agr_company_disposal_users_rel', 'doc_id', 'user_id',
                                               'Кто согласовывает'),
        'agreement_group_ids': fields.many2many('storage.groups', 'agr_company_disposal_groups_rel', 'doc_id', 'group_id',
                                                string='Кто согласовывает группа'),
        'agreement_ids': fields.one2many('cd.disposition.agreement', 'disposition_id', 'Согласование'),
        'access_user_ids': fields.many2many('res.users', 'see_company_disposal_users_rel', 'doc_id', 'user_id', 'Для кого опубликовать'),
        'access_group_ids': fields.many2many('storage.groups', 'see_company_disposal_groups_rel', 'doc_id', 'group_id',
                                             string='Для кого опубликовать группа', domain=[('id', 'in', [111, 22])]),

        'state': fields.selection(STATE, 'Статус'),

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
        'state': 'draft',
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(CdDisposition, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)
        fields = ['from_date', 'on_date', 'from_date_second', 'on_date_second', 'not_later_date', 'not_later_date_second', 'to_date', 'financier_id', 'period_id', 'seeing', 'working_off_dates', 'employee_id', 'job_id', 'next_job_id', 'teacher_job_id', 'department_id', 'next_department_id', 'teacher_department_id', 'trip', 'trip_place', 'grade_id', 'reason', 'remark', 'direction_name', 'at_rate', 'date_ot', 'next_attestation', 'motive_rewarding', 'promotion_type', 'teacher_id', 'financing_source', 'commission_ids', 'term', 'term_str', 'amount', 'statement_date', 'instate_date', 'salary', 'salary_per', 'variable', 'variable_per', 'post_probation_grade_id', 'probation_grade_id', 'duration_probation', 'year', 'no_work', 'work_day', 'fio', 'schedule_date', 'commission_date', 'set_date', 'list_date', 'protocol_date', 'top_date', 'result_date']
        no_change_fields = ['id', 'disposition_date', 'line', 'category_id']
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            cr.execute('SELECT f.name, array_agg(disposition_category_id) FROM disposition_category_fields_relation r LEFT JOIN ir_model_fields f on (f.id=r.field_id) GROUP BY f.name')
            for field, categories in cr.fetchall():
                if field in fields:
                    fields.remove(field)
                if field not in no_change_fields:
                    for node in doc.xpath("//field[@name='{0}']".format(field,)):
                        invisible = [['category_id', 'not in', categories]]
                        modifiers = simplejson.loads(node.get('modifiers')) or {}
                        if modifiers.get('invisible'):
                            modifiers['invisible'] += invisible
                        else:
                            modifiers['invisible'] = invisible
                        node.set('modifiers', simplejson.dumps(modifiers))
            for field in fields:
                for node in doc.xpath("//field[@name='{0}']".format(field,)):
                    node.set('modifiers', simplejson.dumps({'invisible': True}))
            result['arch'] = etree.tostring(doc)
        return result

    def save(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context.get('state'):
            return self.write(cr, uid, ids, {'state': context['state']})
        return False


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


class CdDispositionAgreement(Model):
    _name = 'cd.disposition.agreement'
    _description = u'Распоряжение - Согласование'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.browse(cr, uid, ids, context):
            access = str()

            if data.user_id and data.user_id.id == uid:
                access += 'r'

            val = False
            letter = name[6]

            if letter in access or uid == 1:
                val = True
            res[data.id] = val
        return res

    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'user_id': fields.many2one('res.users', 'Сотрудник'),
        'date_agree': fields.date('Дата подтверждения'),
        'agree': fields.boolean('Подтверждение'),
        'disposition_id': fields.many2one('cd.disposition', 'Распоряжение'),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Согласование',
            type='boolean',
            invisible=True
        ),
    }

    def write(self, cr, user, ids, vals, context=None):
        flag = super(CdDispositionAgreement, self).write(cr, user, ids, vals, context)
        for record in self.read(cr, 1, ids, ['disposition_id']):
            cancel_ids = self.search(cr, 1, [('disposition_id', '=', record['disposition_id'][0])])
            if cancel_ids and flag and set(i['agree'] for i in self.read(cr, 1, cancel_ids, ['agree'])) == set([True]):
                self.pool.get('cd.disposition').write(cr, 1, [record['technique_id'][0]], {'state': 'approval'})
        return flag

    def save(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'agree': True, 'date_agree': datetime.date.today().strftime("%Y/%m/%d")})

    def delete(self, cr, uid, ids, context=None):
        for record in self.read(cr, uid, ids, ['user_id', 'disposition_id']):
            self.pool.get('cd.disposition').write(
                cr,
                uid,
                [record['disposition_id'][0]],
                {
                    'agreement_user_ids': ((3, record['user_id'][0]),),
                    'agreement_ids': ((2, record['id']),)
                })
        return {'type': 'ir.actions.act_window_close'}

CdDispositionAgreement()