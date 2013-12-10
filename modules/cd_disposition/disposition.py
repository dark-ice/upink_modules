# coding=utf-8
import base64
from aeroolib.plugins.opendocument import Template, OOSerializer
from datetime import datetime, date
import math
from pytils import dt, numeral
from notify import notify
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import os
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


def to_grn(amount):
    if amount:
        cash_d = math.modf(amount)
        if round(cash_d[0], 2) != 0.0:
            d = int(round(cash_d[0], 2) * 100)
            if d < 10:
                d = u"0%s" % d
            else:
                d = u"%s" % d
        else:
            d = u"00"
        d += u" коп"
        return u"{0} {1}".format(numeral.in_words(cash_d[1]), d)
    else:
        return '-'


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
        for record in self.browse(cr, uid, ids, context):
            res[record.id] = {
                'check_a': False,
                'check_f': False,
                'check_g': False,
            }

            if record.user_id.id == uid or uid == 1:
                res[record.id]['check_a'] = True

            if uid in (13, 1):
                res[record.id]['check_f'] = True

            if record.category_id.template_id:
                res[record.id]['check_g'] = True

        return res

    _columns = {
        'user_id': fields.many2one('res.users', 'Автор', readonly=True,),
        'disposition_date': fields.date('Дата распоряжения', readonly=True,),
        'line': fields.selection(
            LINES,
            'Направленность',
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'category_id': fields.many2one(
            'cd.disposition.category',
            'Категория',
            domain="[('line', '=', line)]",
            required=True,
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'from_date': fields.date(
            'С какого числа, месяца, года',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'on_date': fields.date(
            'На какое число, месяц, год ',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'from_date_second': fields.date(
            'С какого числа, месяца, года',
            help='20 число месяца',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'on_date_second': fields.date(
            'На какое число, месяц, год ',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'not_later_date': fields.date(
            'Не позднее какой даты?',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'not_later_date_second': fields.date(
            'Уведомить не позже',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'to_date': fields.date(
            'По какое число, месяц, год',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'financier_id': fields.many2one(
            'res.users',
            'Фин. контролер',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'period_id': fields.many2one(
            'kpi.period',
            'За какой месяц, год',
            domain=[('calendar', '=', 'rus')],
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'seeing': fields.text(
            'Причина (в связи с)',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'working_off_dates': fields.char(
            'С отработкой',
            size=256,
            help='Дни для отработки',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'employee_id': fields.many2one(
            'hr.employee',
            'Сотрудник',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'job_id': fields.many2one(
            'hr.job',
            'Должность',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'next_job_id': fields.many2one(
            'hr.job',
            'Новая должность',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'teacher_job_id': fields.many2one(
            'hr.job',
            'Должность наставника',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'department_id': fields.many2one(
            'hr.department',
            'Направление',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'next_department_id': fields.many2one(
            'hr.department',
            'Новое направление',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'teacher_department_id': fields.many2one(
            'hr.department',
            'Направление наставника',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'trip': fields.text(
            'Цель командировки',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'trip_place': fields.text(
            'Место командировки',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'grade_id': fields.many2one(
            'kpi.grade',
            'Грейд, категория',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'reason': fields.text(
            'Основание',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'remark': fields.text(
            'Замечание, выговор, применить удержание',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'direction_name': fields.char(
            'Название направления',
            size=256,
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'at_rate': fields.float(
            'В размере',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'date_ot': fields.date(
            'От какой даты',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'next_attestation': fields.date(
            'Дата следующей аттестации',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'motive_rewarding': fields.text(
            'Мотив награждения',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'promotion_type': fields.text(
            'Вид поощрения',
            help='Объявить благодарность, наградить ценным подарком или почетной грамотой, выдать премию и др',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'teacher_id': fields.many2one(
            'hr.employee',
            'Наставник',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'financing_source': fields.char(
            'Источник финансирования',
            size=256,
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'commission_ids': fields.many2many(
            'res.users',
            'disposition_users_rel',
            'disposition_id',
            'user_id',
            string='Комиссия в составе',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'term': fields.integer(
            'В какой срок',
            help='Кол-во дней',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'term_str': fields.char(
            'В какой срок',
            size=256,
            help='Прописью: в пятидневный срок с момента подписания распоряжения',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'amount': fields.float(
            'Сумма удержания',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'statement_date': fields.date(
            'Заявление от',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'instate_date': fields.date(
            'Дата принятия',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'salary': fields.float(
            'Оклад',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'salary_per': fields.float(
            'Оклад, %',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'variable': fields.float(
            'Переменная часть',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'variable_per': fields.float(
            'Переменная часть, %',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'post_probation_grade_id': fields.many2one(
            'kpi.grade',
            'Грейд, категория после испыт. срока',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'probation_grade_id': fields.many2one(
            'kpi.grade',
            'Грейд, категория на испыт. сроке',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'duration_probation': fields.integer(
            'Длительность испытательного срока',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'year': fields.char(
            'Год',
            size=4,
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'no_work': fields.text(
            'Нерабочие праздничные дни',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'work_day': fields.text(
            'Перенести',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'fio': fields.char(
            'ФИО',
            size=256,
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'schedule_date': fields.date(
            'Утвердить график',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'commission_date': fields.date(
            'Создать аттестационную комиссию',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'set_date': fields.date(
            'Передать',
            help='Бланки самооценки сотрудников и тестовые задания для сотрудников',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'list_date': fields.date(
            'Подготовить и утвердить списки лиц',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'protocol_date': fields.date(
            'Подготовить протоколы',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'top_date': fields.date(
            'Передать генеральному директору',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),
        'result_date': fields.date(
            'Огласить результаты',
            readonly=True,
            states={
                'draft': [('readonly', False)],
            }),

        'agreement_user_ids': fields.many2many('res.users', 'agr_company_disposal_users_rel', 'doc_id', 'user_id',
                                               'Кто согласовывает'),
        'agreement_group_ids': fields.many2many('storage.groups', 'agr_company_disposal_groups_rel', 'doc_id', 'group_id',
                                                string='Кто согласовывает группа'),
        'agreement_ids': fields.one2many('cd.disposition.agreement', 'disposition_id', 'Согласование'),
        'access_user_ids': fields.many2many(
            'res.users',
            'see_company_disposal_users_rel',
            'doc_id',
            'user_id',
            'Для кого опубликовать',
            states={
                'publish': [('readonly', True)],
            }),
        'access_group_ids': fields.many2many(
            'storage.groups',
            'see_company_disposal_groups_rel',
            'doc_id',
            'group_id',
            string='Для кого опубликовать группа',
            domain=[('id', 'in', [111, 22])],
            states={
                'publish': [('readonly', True)],
            }),

        'state': fields.selection(STATE, 'Статус'),
        'disposition': fields.text('Текст распоряжения'),

        'check_f': fields.function(
            check_access,
            method=True,
            string="Проверка на ГД",
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
        'check_g': fields.function(
            check_access,
            method=True,
            string="Проверка на возможность генерировать",
            type="boolean",
            invisible=True,
            multi='check',
        ),

        'doc_id': fields.many2one('ir.attachment', 'Распоряжение', readonly=True),
        'index_content': fields.related(
            'doc_id',
            'index_content',
            type='text',
            readonly=True
        ),
        'screen_id': fields.related(
            'category_id',
            'screen_id',
            'datas',
            type='binary',
            readonly=True
        ),
        'history_ids': fields.one2many(
            'cd.disposition.history',
            'disposition_id',
            string='История',
            readonly=True
        )
    }

    _defaults = {
        'user_id': lambda s, cr, u, cntx: u,
        'disposition_date': lambda *a: fields.date.today(),
        'state': 'draft',
        'check_a': True,
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(CdDisposition, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)
        disposition_fields = ['from_date', 'on_date', 'from_date_second', 'on_date_second', 'not_later_date', 'not_later_date_second', 'to_date', 'financier_id', 'period_id', 'seeing', 'working_off_dates', 'employee_id', 'job_id', 'next_job_id', 'teacher_job_id', 'department_id', 'next_department_id', 'teacher_department_id', 'trip', 'trip_place', 'grade_id', 'reason', 'remark', 'direction_name', 'at_rate', 'date_ot', 'next_attestation', 'motive_rewarding', 'promotion_type', 'teacher_id', 'financing_source', 'commission_ids', 'term', 'term_str', 'amount', 'statement_date', 'instate_date', 'salary', 'salary_per', 'variable', 'variable_per', 'post_probation_grade_id', 'probation_grade_id', 'duration_probation', 'year', 'no_work', 'work_day', 'fio', 'schedule_date', 'commission_date', 'set_date', 'list_date', 'protocol_date', 'top_date', 'result_date']
        no_change_fields = ['id', 'disposition_date', 'line', 'category_id']
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            cr.execute('SELECT f.name, array_agg(disposition_category_id) FROM disposition_category_fields_relation r LEFT JOIN ir_model_fields f on (f.id=r.field_id) GROUP BY f.name')
            for field, categories in cr.fetchall():
                if field in disposition_fields:
                    disposition_fields.remove(field)
                if field not in no_change_fields:
                    for node in doc.xpath("//field[@name='{0}']".format(field,)):
                        invisible = [['category_id', 'not in', categories]]
                        modifiers = simplejson.loads(node.get('modifiers')) or {}
                        if modifiers.get('invisible'):
                            modifiers['invisible'] += invisible
                        else:
                            modifiers['invisible'] = invisible
                        node.set('modifiers', simplejson.dumps(modifiers))
            for field in disposition_fields:
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

    def generate_file(self, cr, uid, ids, context=None):
        doc_id = self.generate(cr, uid, ids)
        if doc_id:
            return self.write(cr, uid, ids, {'doc_id': doc_id})
        return False

    # генерируем odt
    def generate(self, cr, user, ids, context=None):
        disposition_id = ids
        if isinstance(ids, (list, tuple)):
            disposition_id = ids[0]
        disposition = self.read(cr, user, disposition_id, [])

        category = self.pool.get('cd.disposition.category').read(cr, user, disposition['category_id'][0], ['template_id'])
        if category['template_id']:
            template = self.pool.get('ir.attachment').read(cr, user, category['template_id'][0],
                                                           ['store_fname', 'parent_id'])
            dbro = self.pool.get('document.directory').read(cr, user, template['parent_id'][0], ['storage_id'], context)
            storage = self.pool.get('document.storage').read(cr, user, dbro['storage_id'][0], ['path'])

            filepath = os.path.join(storage['path'], template['store_fname'])
            file_data = open(filepath, 'rb').read()
            template_io = StringIO()
            template_io.write(file_data)
            serializer = OOSerializer(template_io)
            basic = Template(source=template_io, serializer=serializer)

            o = {
                'disposition_number': disposition['id'],
                'disposition_date': dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['disposition_date'], '%Y-%m-%d'), inflected=True),
                'from_date': '-',
                'on_date': '-',
                'from_date_second': '-',
                'on_date_second': '-',
                'not_later_date': '-',
                'not_later_date_second': '-',
                'to_date': '-',
                'financier_id': '-',
                'period_id': '-',
                'seeing': disposition['seeing'] or '-',
                'working_off_dates': disposition['working_off_dates'] or '-',
                'employee_id': '-',
                'job_id': '-',
                'next_job_id': '-',
                'teacher_job_id': '-',
                'department_id': '-',
                'next_department_id': '-',
                'teacher_department_id': '-',
                'trip': disposition['trip'] or '-',
                'trip_place': disposition['trip_place'] or '-',
                'grade_id': '-',
                'reason': disposition['reason'] or '-',
                'remark': disposition['remark'] or '-',
                'direction_name': disposition['direction_name'] or '-',
                'at_rate': disposition['at_rate'] or '-',
                'date_ot': '-',
                'next_attestation': '-',
                'motive_rewarding': disposition['motive_rewarding'] or '-',
                'promotion_type': disposition['promotion_type'] or '-',
                'teacher_id': '-',
                'financing_source': disposition['financing_source'] or '-',
                'commission_ids': '-',
                'term': disposition['term'] or '-',
                'term_str': disposition['term_str'] or '-',
                'amount': disposition['amount'] or '-',
                'amount_str': to_grn(disposition['at_rate']),
                'statement_date': '-',
                'instate_date': '-',
                'salary': disposition['salary'] or '-',
                'salary_per': disposition['salary_per'] or '-',
                'variable': disposition['variable'] or '-',
                'variable_per': disposition['variable_per'] or '-',
                'post_probation_grade_id': '-',
                'probation_grade_id': '-',
                'duration_probation': disposition['duration_probation'] or '-',
                'year': disposition['year'] or '-',
                'no_work': disposition['no_work'] or '-',
                'work_day': disposition['work_day'] or '-',
                'fio': disposition['fio'] or '-',
                'schedule_date': '-',
                'commission_date': '-',
                'set_date': '-',
                'list_date': '-',
                'protocol_date': '-',
                'top_date': '-',
                'result_date': '-'
            }

            if disposition['from_date']:
                o['from_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['from_date'], '%Y-%m-%d'), inflected=True)
            if disposition['on_date']:
                o['on_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['on_date'], '%Y-%m-%d'), inflected=True)
            if disposition['from_date_second']:
                o['from_date_second'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['from_date_second'], '%Y-%m-%d'), inflected=True)
            if disposition['on_date_second']:
                o['on_date_second'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['on_date_second'], '%Y-%m-%d'), inflected=True)
            if disposition['not_later_date']:
                o['not_later_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['not_later_date'], '%Y-%m-%d'), inflected=True)
            if disposition['not_later_date_second']:
                o['not_later_date_second'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['not_later_date_second'], '%Y-%m-%d'), inflected=True)
            if disposition['to_date']:
                o['to_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['to_date'], '%Y-%m-%d'), inflected=True)
            if disposition['date_ot']:
                o['date_ot'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['date_ot'], '%Y-%m-%d'), inflected=True)
            if disposition['next_attestation']:
                o['next_attestation'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['next_attestation'], '%Y-%m-%d'), inflected=True)
            if disposition['statement_date']:
                o['statement_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['statement_date'], '%Y-%m-%d'), inflected=True)
            if disposition['instate_date']:
                o['instate_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['instate_date'], '%Y-%m-%d'), inflected=True)
            if disposition['schedule_date']:
                o['schedule_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['schedule_date'], '%Y-%m-%d'), inflected=True)
            if disposition['commission_date']:
                o['commission_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['commission_date'], '%Y-%m-%d'), inflected=True)
            if disposition['set_date']:
                o['set_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['set_date'], '%Y-%m-%d'), inflected=True)
            if disposition['list_date']:
                o['list_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['list_date'], '%Y-%m-%d'), inflected=True)
            if disposition['protocol_date']:
                o['protocol_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['protocol_date'], '%Y-%m-%d'), inflected=True)
            if disposition['top_date']:
                o['top_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['top_date'], '%Y-%m-%d'), inflected=True)
            if disposition['result_date']:
                o['result_date'] = dt.ru_strftime(u"%d %B %Y", datetime.strptime(disposition['result_date'], '%Y-%m-%d'), inflected=True)
            if disposition['financier_id']:
                o['financier_id'] = disposition['financier_id'][1]
            if disposition['employee_id']:
                o['employee_id'] = disposition['employee_id'][1]
            if disposition['job_id']:
                o['job_id'] = disposition['job_id'][1]
            if disposition['teacher_id']:
                o['teacher_id'] = disposition['teacher_id'][1]
            if disposition['next_job_id']:
                o['next_job_id'] = disposition['next_job_id'][1]
            if disposition['teacher_job_id']:
                o['teacher_job_id'] = disposition['teacher_job_id'][1]
            if disposition['department_id']:
                o['department_id'] = disposition['department_id'][1]
            if disposition['next_department_id']:
                o['next_department_id'] = disposition['next_department_id'][1]
            if disposition['teacher_department_id']:
                o['teacher_department_id'] = disposition['teacher_department_id'][1]
            if disposition['grade_id']:
                o['grade_id'] = disposition['grade_id'][1]
            if disposition['post_probation_grade_id']:
                o['post_probation_grade_id'] = disposition['post_probation_grade_id'][1]
            if disposition['probation_grade_id']:
                o['probation_grade_id'] = disposition['probation_grade_id'][1]
            if disposition['commission_ids']:
                o['commission_ids'] = ', '.join([x['name'] for x in self.pool.get('res.users').read(cr, 1, disposition['commission_ids'], ['name'])])
            if disposition['period_id']:
                d = datetime.strptime('2013/10', '%Y/%m').strftime('%B %Y')
                o['period_id'] = tools.ustr(d)

            filename = 'Распоряжение № {0}'.format(disposition['id'],)

            odt_file = os.path.join(storage['path'], 'tmp.odt')
            file(odt_file, 'wb').write(basic.generate(o=o).render().getvalue())

            doc_id = self.pool.get('ir.attachment').create(cr, user, {
                'name': '{0}.odt'.format(filename, ),
                'datas': base64.b64encode(open(odt_file, 'rb').read()),
                'datas_fname': '{0}.odt'.format(filename, ),
                'res_model': self._name,
                'res_id': disposition['id']
            })
            #self.write(cr, user, [disposition['id']], {'doc_id': doc_id})
            return doc_id
        return False

    @notify.msg_send(_name)
    def write(self, cr, user, ids, vals, context=None):
        for record in self.read(cr, user, ids, []):
            action = ''
            errors = []
            state = record['state']
            next_state = vals.get('state')

            if next_state == 'agreement' and state == 'draft':
                doc_id = self.generate(cr, user, record['id'])
                if doc_id:
                    vals['doc_id'] = doc_id

                if not vals.get('agreement_ids') and not record['agreement_ids']:
                    errors.append('Необходимо выбрать людей для согласования распоряжения.')
            if next_state == 'publish':
                if not vals.get('access_user_ids') and not vals.get('access_group_ids') and not record['access_user_ids'] and not record['access_group_ids']:
                    errors.append('Необходимо выбрать тех кто может видеть распоряжение.')

            if errors:
                raise osv.except_osv('Распоряжения', ' '.join(errors))

            if next_state and next_state != state:
                action = "{state} -> {next_state}".format(state=dict(STATE)[state], next_state=dict(STATE)[next_state])
            if action:
                vals['history_ids'] = [(0, 0, {'name': action, 'state': next_state})]
        return super(CdDisposition, self).write(cr, user, ids, vals, context)

    def change_category(self, cr, uid, ids, category_id, context=None):
        vals = {}
        category = self.pool.get('cd.disposition.category').browse(cr, uid, category_id)
        if category and category.template_id:
            vals['check_g'] = True,
            if category.screen_id:
                vals['screen_id'] = category.screen_id.datas

        return {'value': vals}

CdDisposition()


class CdDispositionCategory(Model):
    _name = 'cd.disposition.category'
    _description = u'Распоряжения - Категории'

    _columns = {
        'line': fields.selection(LINES, 'Направленность', required=True),
        'name': fields.char('Название', size=256),
        'template_id': fields.many2one('ir.attachment', 'Файл шаблона договора'),
        'screen_id': fields.many2one('ir.attachment', 'Скриншот шаблона договора'),
        'field_ids': fields.many2many(
            'ir.model.fields',
            'disposition_category_fields_relation',
            'disposition_category_id',
            'field_id',
            'Доступные поля',
            domain=['&', ('model_id', '=', 'cd.disposition'), '!', ('name', 'ilike', 'check'), ('name', 'not in', ['history_ids', 'screen_id', 'index_content', 'doc_id', 'state', 'access_group_ids', 'access_user_ids', 'agreement_ids', 'agreement_group_ids', 'agreement_user_ids', 'category_id', 'line', 'disposition_date', 'user_id'])]),
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
            if cancel_ids and flag and set(i['agree'] for i in self.read(cr, 1, cancel_ids, ['agree'])) == {True}:
                self.pool.get('cd.disposition').write(cr, 1, [record['disposition_id'][0]], {'state': 'approval'})
        return flag

    def save(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'agree': True, 'date_agree': date.today().strftime("%Y/%m/%d")})

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


class CdDispositionHistory(Model):
    _name = 'cd.disposition.history'
    _description = u'Распоряжение - История'

    _columns = {
        'create_uid': fields.many2one('res.users', 'Автор', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.char('Действие', size=256),
        'state': fields.char('Этап', size=256),
        'employee_id': fields.integer('Сотрудник'),
        'disposition_id': fields.many2one('cd.disposition', 'Распоряжение'),
    }
CdDispositionHistory()