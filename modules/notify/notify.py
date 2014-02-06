# -*- coding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields
from openerp.osv.orm import Model
from mako.template import Template


class Notify(Model):
    _name = 'notify'
    _description = u"Уведомления"
    _order = "model, id"
    _log_create = True

    _columns = {
        'model': fields.many2one('ir.model', u'Модель', required=True),
        'type': fields.selection([
            ('workflow', u'Переход с этапа'),
            ('change', u'Изменение поля'),
            ('everyone', u'Каждое сохранение'),
        ], u'Тип сообщений'),
        'mail': fields.boolean(u'Внешняя почта'),
        'skype': fields.boolean(u'Skype'),
        'name': fields.char(u'Тема сообщения', size=250),
        'message': fields.text(u'Сообщение'),
        'workflow': fields.many2one('workflow', u'Процесс'),
        'transition': fields.many2one('workflow.transition', u'Переходы'),
        'from_state': fields.char(u'С этапа', size=50),
        'to_state': fields.char(u'На этап', size=50),

        'send_group_ids': fields.many2many(
            'res.groups',
            'send_group_rel',
            'group_id',
            'notify_id',
            u'Группа для отправки'),
        'send_field_ids': fields.many2many(
            'ir.model.fields',
            'send_field_rel',
            'field_id',
            'notify_id',
            u'Брать из поля'
        ),
        'send_users': fields.many2many(
            'res.users',
            'send_users_rel',
            'user_id',
            'notify_id',
            u'Пользователи для отправки'
        ),
        'ignore_users': fields.many2many(
            'res.users',
            'ignore_users_rel',
            'user_id',
            'notify_id',
            u'Кроме пользователей'
        ),

        'changed_field': fields.many2one('ir.model.fields', u'Изменяемое поле'),
        'clear_field': fields.boolean(u'Очистить поле'),

        # Fake fields used to implement the placeholder assistant
        'model_object_field': fields.many2one(
            'ir.model.fields',
            string=u"Поле"
        ),
        'sub_object': fields.many2one(
            'ir.model',
            u'Связанная модель',
            readonly=True),
        'sub_model_object_field': fields.many2one(
            'ir.model.fields',
            u'Поле в связанной модели'),
        'null_value': fields.char(
            u'Нулевое значение',
            size=128
        ),
        'copyvalue': fields.char(
            u'Готовый тег',
            size=256
        ),
        'active': fields.boolean('Активно'),
        'send': fields.boolean('Отправлять'),
        'condition': fields.text('Условия отправки сообщения', help='data - dict'),
    }

    _defaults = {
        'mail': True,
        'active': True,
        'send': True,
    }

    def change_type(self, cr, uid, ids, type):
        v = {'type': type}
        return {'value': v}

    def change_model(self, cr, uid, ids, model):
        if model:
            model_data = self.pool.get('ir.model').browse(cr, 1, model)
            wkf_id = self.pool.get('workflow').search(cr, 1, [('osv', '=', model_data.model)])
            if wkf_id:
                return {'value': {'workflow': wkf_id[0]}, 'domain': {'transition': [('wkf_id', '=', wkf_id[0])]}}
            else:
                return {'value': {'workflow': '', 'transition': '', 'from_state': '', 'to_state': ''}}

    def change_transition(self, cr, uid, ids, transition):
        if transition:
            wkf_transition = self.pool.get('workflow.transition').browse(cr, 1, transition)
            if wkf_transition:
                v = {'from_state': wkf_transition.act_from.name, 'to_state': wkf_transition.act_to.name}
            else:
                v = {'from_state': '', 'to_state': ''}
            return {'value': v}

    def build_expression(self, field_name, sub_field_name, null_value):
        """Returns a placeholder expression for use in a template field,
           based on the values provided in the placeholder assistant.

          :param field_name: main field name
          :param sub_field_name: sub field name (M2O)
          :param null_value: default value if the target value is empty
          :return: final placeholder expression
        """
        expression = ''
        if field_name:
            expression = "${object." + field_name
            if sub_field_name:
                expression += "." + sub_field_name
            if null_value:
                expression += " or '''%s'''" % null_value
            expression += "}"
        return expression

    def onchange_sub_model_object_value_field(self, cr, uid, ids, model_object_field, sub_model_object_field=False, null_value=None, context=None):
        result = {
            'sub_object': False,
            'copyvalue': False,
            'sub_model_object_field': False,
            'null_value': False
        }
        if model_object_field:
            fields_obj = self.pool.get('ir.model.fields')
            field_value = fields_obj.browse(cr, uid, model_object_field, context)
            if field_value.ttype in ['many2one', 'one2many', 'many2many']:
                res_ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', field_value.relation)], context=context)
                sub_field_value = False
                if sub_model_object_field:
                    sub_field_value = fields_obj.browse(cr, uid, sub_model_object_field, context)
                if res_ids:
                    result.update({
                        'sub_object': res_ids[0],
                        'copyvalue': self.build_expression(field_value.name, sub_field_value and sub_field_value.name or False, null_value or False),
                        'sub_model_object_field': sub_model_object_field or False,
                        'null_value': null_value or False
                    })
            else:
                result.update({
                    'copyvalue': self.build_expression(field_value.name, False, null_value or False),
                    'null_value': null_value or False
                })
        return {'value': result}

    def write(self, cr, uid, ids, values, context=None):
        data = self.browse(cr, uid, ids[0])
        model = values['model'] if values.get('model', False) else data.model
        if model:
            if isinstance(model, (int, long)):
                model_id = model
                model = self.pool.get('ir.model').browse(cr, 1, model_id)

            wkf_id = self.pool.get('workflow').search(cr, 1, [('osv', '=', model.model)])
            if wkf_id:
                values['workflow'] = wkf_id[0]
                transition = values['transition'] if values.get('transition', False) else data.transition
                if isinstance(transition, (int, long)):
                    transition_id = transition
                    transition = self.pool.get('workflow.transition').browse(cr, 1, transition_id)

                if transition:
                    values['from_state'] = transition.act_from.name
                    values['to_state'] = transition.act_to.name
                else:
                    values['from_state'] = ''
                    values['to_state'] = ''
                if 'transition' in values.keys() and not values.get('transition', False) and data.transition:
                    values['from_state'] = ''
                    values['to_state'] = ''

            else:
                values['workflow'] = ''
                values['transition'] = ''
                values['from_state'] = ''
                values['to_state'] = ''

        return super(Notify, self).write(cr, uid, ids, values, context)

    def get_employers(self, cr, user, notify, data, values):
        employee_pool = self.pool.get('hr.employee')
        my_employee = employee_pool.get_employee(cr, user, user)
        employers = []
        ignore_employers = []
        tmp_employers = []
        if notify.ignore_users:
            ignore_employers = [employee_pool.get_employee(cr, user, u.id) for u in notify.ignore_users]

        if notify.send_users:
            employers = [employee_pool.get_employee(cr, user, u.id) for u in notify.send_users]

        if notify.send_group_ids:
            employers += [employee_pool.get_employee(cr, user, u.id) for group in notify.send_group_ids for u in group.users]

        if notify.send_field_ids:
            for field in notify.send_field_ids:
                record = values[field.name] if values.get(field.name, False) else data.get(field.name, False)
                if isinstance(record, tuple):
                    tmp_employers.append((record[0], field.relation))
                elif isinstance(record, list):
                    for u in record:
                        if isinstance(u, (int, long)):
                            tmp_employers += [(u, field.relation)]
                        elif isinstance(u, list):
                            tmp_employers += [(x, field.relation) for x in u[2]]
                        else:
                            tmp_employers += [(u.id, field.relation)]
                else:
                    tmp_employers.append((record, field.relation))

        for emp in tmp_employers:
            if emp[1] == 'hr.employee':
                employers.append(employee_pool.browse(cr, 1, emp[0]))
            elif emp[1] == 'res.users':
                employers.append(employee_pool.get_employee(cr, user, emp[0]))
            elif emp[1] == 'res.groups':
                employers = [employee_pool.get_employee(cr, user, u.id)
                             for u in self.pool.get('res.groups').browse(cr, 1, emp[0]).users]
            elif emp[1] == 'storage.groups':
                ug = self.pool.get('storage.groups').browse(cr, 1, emp[0])
                if ug.is_all:
                    all_ids = employee_pool.search(cr, 1, [])
                    employers += [employee_pool.browse(cr, 1, emp.id) for emp in employee_pool.browse(cr, 1, all_ids)]
                else:
                    employers += [employee_pool.get_employee(cr, user, u.id) for u in ug.users_group]

            if my_employee in employers:
                employers.remove(my_employee)
            employers = [emp for emp in employers if emp not in ignore_employers]
        return filter(lambda x: x, employers)

    def send(self, cr, uid, model_name, data, values):
        model_pool = self.pool.get('ir.model')
        model_ids = model_pool.search(cr, 1, [('model', '=', model_name)])
        model = model_pool.browse(cr, 1, model_ids[0])
        notify_ids = self.search(cr, 1, [('model', '=', model.id), ('active', '=', True)])
        act_from = data.get('state', False)
        act_to = values.get('state', False)

        notify = None
        for n in self.browse(cr, 1, notify_ids):
            if n.type == 'workflow' and n.transition and act_from and act_to:
                if act_from in n.transition.act_from.action and act_to in n.transition.act_to.action:
                    notify = n
                    break
            elif n.type == 'change' and n.changed_field.name in values:
                notify = n
                if n.clear_field:
                    values[n.changed_field.name] = False
                break
            elif n.type == 'everyone':
                notify = n
                break

        if notify:
            send_flag = False
            if not notify.condition:
                send_flag = True
            else:
                notify.condition = 'flag = {condition}'.format(condition=notify.condition)
                exec compile(notify.condition, '<string>', 'exec')
                if flag:
                    send_flag = True

            if send_flag:
                employers = self.get_employers(
                    cr,
                    uid,
                    notify,
                    data,
                    values
                )

                message = self.pool.get('mail.message')
                ir_mail_server = self.pool.get('ir.mail_server')
                server_id = ir_mail_server.search(cr, 1, [], limit=1)[0]

                href = "<a href='http://46.28.67.245:8069/web/webclient/home#id=%s&view_type=page&model=%s'>" % (data['id'], model_name)

                emails_list = []
                emails_tmp = []
                email_str = ''

                if employers:
                    emails_q = [emp.work_email for emp in employers if emp.work_email]
                    for record in emails_q:
                        email_str += ',' + record
                        if len(email_str) > 250:
                            emails_list.append(emails_tmp)
                            emails_tmp = []
                            email_str = ''
                        emails_tmp.append(record)
                    emails_list.append(emails_tmp)

                msg_ids = []

                for emails in emails_list:
                    msg_ids.append(message.schedule_with_attach(
                        cr,
                        1,
                        ir_mail_server.browse(cr, 1, server_id).smtp_user,
                        emails,
                        Template(
                            notify.name,
                            default_filters=['decode.utf8']).render_unicode(
                                a=href,
                                object=self.pool.get(model_name).browse(cr, 1, data['id'])
                            ),
                        Template(
                            notify.message,
                            default_filters=['decode.utf8']).render_unicode(
                                a=href,
                                object=self.pool.get(model_name).browse(cr, 1, data['id'])
                            ),
                        model=model_name,
                        res_id=data['id'],
                        subtype='html'
                    ))

                if notify.send:
                    message.send(cr, 1, msg_ids)
        return values

Notify()


def msg_send(model_name='', workflow_name=''):
    """
    Декоратор для отправки сообщений для справочник контроля по бизнес-процессам (переходов и выполнения).
    @param model_name: Модель для которой добавляется
    @param workflow_name: Наименование workflow модели (убираем :) )
    """

    def send_decorator(fn):
        """
        @param fn: Функция, которую декорируем. теперь это write!
        """

        def wrapper(*args, **kwargs):
            """
            @param args: аргументы получаемые декорируемой функцией, их 4:
             args[0] = self(объект модели)
             args[1] = cr
             args[2] = uid
             args[3] = ids
             args[4] = values
            """
            if args[3]:
                notify_pool = args[0].pool.get('notify')
                model_data = args[0].pool.get(model_name).read(args[1], 1, args[3][0], [])

                new_args = list(args)
                if model_data:
                    new_args[4] = notify_pool.send(args[1], args[2], model_name, model_data, args[4])
                    return fn(*new_args, **kwargs)
                else:
                    return fn(*args, **kwargs)

        return wrapper
    return send_decorator


class NotifyService(netsvc.Service):
    def __init__(self, name='notify'):
        netsvc.Service.__init__(self, name)
        self.ntf_on_create_cache = {}

    def clear_cache(self, cr, uid):
        self.ntf_on_create_cache[cr.dbname] = {}

NotifyService()
