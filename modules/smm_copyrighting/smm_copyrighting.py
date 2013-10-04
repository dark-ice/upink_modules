# -*- encoding: utf-8 -*-
from osv import fields, osv
from datetime import datetime, timedelta
from openerp import tools
import pytz

tzlocal = pytz.timezone(tools.detect_server_timezone())


class group_agents_stage(osv.osv):
    _name = "group.agents.stage"
    _description = u"СММ копирайтинг - Группа исполнителя"
    _rec_name = "agent_group_id"
    _columns = {
        'agent_group_id': fields.many2one('res.groups', 'Группа исполнителя', required=True),
    }

    def _constraint_unique(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            unique_id = self.search(cr, uid, [])
            if unique_id != ids:
                return False
        return True
    _constraints = [
        (_constraint_unique,
         'Запись может быть только одна.',
         []),
    ]

group_agents_stage()


class smm_copyright_history(osv.osv):
    _name = 'smm.copyright.history'
    _columns = {
        'usr_id': fields.many2one('res.users', 'Перевел'),
        'create_date': fields.datetime('Дата создания'),
        'state': fields.char('На этап', size=65),
        'state_id': fields.char('Этап', size=65),
        'smm_copyright_id': fields.many2one('smm.copyrighting', 'SMM copyright', invisible=True),
    }

    _order = "create_date desc"

smm_copyright_history()


class smm_copyright_messages(osv.osv):
    _name = 'smm.copyright.messages'

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

    _columns = {
        'usr_id': fields.many2one('res.users', 'Автор', readonly=True),
        'cr_date': fields.datetime('Дата создания', readonly=True),
        'text': fields.text('Комментарий'),
        #'rep_file_id': fields.many2one('attach.files', 'Файл'),
        'smm_copyright_id': fields.many2one('smm.copyrighting', 'SMM copyright', invisible=True),
    }

    _rec_name = 'cr_date'

    _defaults = {
        'usr_id': lambda self, cr, uid, context: uid,
        'cr_date': datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

    _order = "cr_date desc"

smm_copyright_messages()


class smm_copyrighting(osv.osv):
    _name = "smm.copyrighting"
    _description = u"Социальные сети - копирайтинг"

    workflow_name = 'wkf_smm_copyrighting'

    state_first = {
        'draft': 'черновик',
        'acceptance_application': 'принятие заявки',
        'application_on_completion': 'заявка на доработке',
        'prep_to_start': 'подготовка задания к выполнению',
        'writing_text': 'написание текста',
        'approval_text': 'согласование текста',
        'text_on_completion_app': 'доработка текста(согласование)',
        'adoption_text': 'утверждение текста',
        'text_on_completion_adop': 'доработка текста(утверждение)',
        'not_important': 'задание не актуально',
        'closed': 'текст утвержден',
    }

    def check_autor_editor(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        id_res = self.pool.get('ir.model.data').search(cr, uid, [('name', '=', 'smm_editor'), ('model', '=', 'res.groups')])[0]
        id_group = self.pool.get('ir.model.data').read(cr, uid, id_res, ['res_id'])['res_id']
        res_user_g = self.pool.get('res.users').read(cr, uid, uid, ['groups_id'])['groups_id']
        if data.user_id.id == uid or id_group in res_user_g:
            return True
        return False

    def check_autor(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        if data.user_id.id == uid:
            return True
        return False

    def onchange_filename(self, cr, uid, ids, field_name, filename, context=None):
        res = {}
        if filename:
            res[field_name] = filename.split('\\')[-1]
        return {'value': res}

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

    def project_deadlines(self, cr, uid, context=None):
        return False

    def workflow_setter(self, cr, uid, ids, state=None):
        self.write(cr, uid, ids, {'state': state, 'deadline': False})
        return True

    def timedelta_type(self, time_type, time):
        # Check time_type and
        # return appropriate timedelta object
        if time_type == 'hours':
            return timedelta(hours=time)
        elif time_type == 'minutes':
            return timedelta(minutes=time)
        elif time_type == 'days':
            return timedelta(days=time)

    def get_time(self, current_time, control_time=False):
        # recursive check if current time is in range 9-18
        # if no control_time return current_time
        def get_day(current_time):
            # define special conditions for friday, saturday, sunday
            day = current_time.isoweekday()
            if day == 7:
                return 1
            elif day == 6:
                return 2
            elif day == 5:
                return 3
            return False
        next_day = get_day(current_time)
        if current_time > current_time.replace(hour=18, minute=0):
            next_day = next_day or 1
            control_time = (current_time - current_time.replace(hour=18, minute=0)) if not control_time else control_time
            current_time = current_time.replace(hour=9, minute=0) + timedelta(days=next_day)
        #~ elif current_time < current_time.replace(hour=9, minute=0) or next_day:
            #~ next_day = next_day or 0
            #~ current_time = current_time.replace(hour=9, minute=0) + timedelta(days=next_day)
        if not control_time:
            return current_time
        current_time = current_time + control_time
        return self.get_time(current_time)

    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор заявки', select=True),
        'create_date': fields.datetime('Дата создания', select=True),
        'agent_id': fields.many2one('res.users', 'Исполнитель', select=True),
        'partner_id': fields.many2one('res.partner', 'Партнер', select=True, domain="[('partner_type','=','upsale')]"),
        'site': fields.char('Сайт', size=255),

        'manager_work_id': fields.many2one('res.users', 'Менеджер по работе с партнерами', select=True),
        'manager_upwork_id': fields.related('partner_id', 'user_id', type="many2one", relation="res.users", string="Менеджер по развитию партнеров", store=False, readonly=True),

        'order_type': fields.selection([
            ('external', 'внешний'),
            ('internal', 'внутренний')], 'Тип заказа', select=True),
        'tz_name': fields.char('ТЗ по написанию текста', size=250),
        'tz': fields.binary('Файл'),
        'text_wr_name': fields.char('Написанный текст', size=250),
        'text_wr': fields.binary('Файл'),
        #'rep_file_id': fields.one2many('attach.files', 'obj_id', 'Написанный текст'),
        'date_customer': fields.datetime('Дата желаемого выполнения'),
        'date_runtime': fields.datetime('Дата выполнения'),
        'comment': fields.text('Комментарий по доработке'),
        'state': fields.selection(
            [
                ('draft', 'черновик'),
                ('acceptance_application', 'принятие заявки'),
                ('application_on_completion', 'заявка на доработке'),
                ('prep_to_start', 'подготовка задания к выполнению'),
                ('writing_text', 'написание текста'),
                ('approval_text', 'согласование текста'),
                ('text_on_completion_app', 'доработка текста(согласование)'),
                ('adoption_text', 'утверждение текста'),
                ('text_on_completion_adop', 'доработка текста(утверждение)'),
                ('not_important', 'задание не актуально'),
                ('closed', 'текст утвержден'),
            ], 'статус', readonly=True),
        # Дедлайн для выполнения заданий
        'deadline': fields.datetime('Дедлайн на следующее состояние', readonly=True),

        'history_ids': fields.one2many('smm.copyright.history', 'smm_copyright_id', 'История'),
        'message_ids': fields.one2many('smm.copyright.messages', 'smm_copyright_id', 'Переписка по проекту'),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        #'group_id': lambda self, cr, uid, context: self.pool.get('group.agents.stage').read(cr, uid, self.pool.get('group.agents.stage').search(cr,uid,[], limit=1)[0], ['agent_group_id'])['agent_group_id'][0],
        'state': 'draft',
    }

    def write(self, cr, uid, ids, values, context=None):
        if (not values.get('text_wr_name', False) and values.get('text_wr', False)) or ('text_wr' in values and not values.get('text_wr', False)):
            values.pop('text_wr')
        if (not values.get('tz_name', False) and values.get('tz', False)) or ('tz' in values and not values.get('tz', False)):
            values.pop('tz')

        if 'tz' or 'text_wr' in values:

            field = self.browse(cr, uid, ids[0])
            if 'tz' in values and field.state not in ('draft', 'application_on_completion'):
                values.pop('tz')
            if 'text_wr' in values and field.user_id == uid and (field.state not in ('writing_text', 'text_on_completion_app', 'text_on_completion_adop') or field.state in ('closed', 'not_important')):
                values.pop('text_wr')

        if values.get('state', False) and values.get('state', False) != 'draft':
            field = self.browse(cr, uid, ids[0])
            if values.get('state', False) == 'writing_text' and not field.agent_id and not values.get('agent_id', False):
                raise osv.except_osv("Назначение исполнителя", 'Необходимо назначить исполнителя')
                return False
            if values.get('state', False) == 'approval_text' and not field.text_wr and not values.get('text_wr', False):
                raise osv.except_osv("Написанный текст", 'Необходимо вложить файл с написанным текстом')
                return False
            if values.get('state', False) in ('application_on_completion', 'text_on_completion_app', 'text_on_completion_adop') and not field.comment and not values.get('comment', False):
                raise osv.except_osv("Комментарий по доработке", 'Необходимо ввести комментарий на доработку')
                return False
            if values.get('state', False) in ('prep_to_start', 'adoption_text') and field.comment and not values.get('text_wr', False):
                values.update({'comment': ''})

        if values.get('state', False):
            state = values.get('state', False)
            values.update({'history_ids': [(0, 0, {'usr_id': uid, 'state': self.state_first[state], 'state_id': state})]})

        return super(smm_copyrighting, self).write(cr, uid, ids, values, context)

smm_copyrighting()


