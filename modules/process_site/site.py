# coding=utf-8
import sys
from datetime import datetime as dt
import pytz
from openerp import netsvc, tools
from openerp.osv import fields, osv
from openerp.osv.orm import Model, AbstractModel
from notify import notify

wf_service = netsvc.LocalService("workflow")

STATES = (
    ('draft', 'Не начат'),
    ('work', 'В процессе'),
    ('in_approval', 'На утверждении'),
    ('rectification', 'Исправления'),
    ('project_closure', 'Закрытие проекта'),
    ('closed', 'Проект закрыт'),
)

SUB_STATES = (
    ('none', 'Отсутствует'),
    ('draft', 'Не начат'),
    ('work', 'В процессе'),
    ('in_approval', 'На утверждении'),
    ('rectification', 'Исправления'),
    ('approved', 'Утвержден'),
    ('finish', 'Этап окончен'),
)

V1_STATES = SUB_STATES

V2_STATES = (
    SUB_STATES[0],
    SUB_STATES[1],
    SUB_STATES[2],
    SUB_STATES[3],
    SUB_STATES[6],
)

PLANNING_STATES = V1_STATES
DESIGN_STATES = V1_STATES
TESTING_STATES = V1_STATES

MAKEUP_STATES = V2_STATES
DEVELOPING_STATES = V2_STATES

STAGES = (
    ('planning', 'Проектирование'),
    ('design', 'Дизайн'),
    ('makeup', 'Верстка'),
    ('developing', 'Программирование'),
    ('testing', 'Тестирование'),
)


def get_state(states, state):
    return [item for item in states if item[0] == state][0]


class ProcessSite(Model):
    _name = 'process.site'
    _inherit = 'process.base'
    _description = u'Процессы - Site'

    def _get_attach(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['stage_ids']):
            val = []
            for stage in self.pool.get('process.site.stage').read(cr, uid, record['stage_ids'], ['stage_model', 'stage_id', 'stage']):
                val.extend([(4, i) for i in self.pool.get(stage['stage_model']).read(cr, 1, stage['stage_id'], ['signed_file_ids'])['signed_file_ids']])

            res[record['id']] = val
        return res

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['responsible_id', 'specialist_id', 'service_head_id', 'stage_ids'], context):
            access = str()

            #  Специалист
            if (data.get('specialist_id') and data['specialist_id'][0] == uid) or (data.get('service_head_id') and data['service_head_id'][0] == uid):
                access += 's'

            stage_list = set([
                get_state(
                    SUB_STATES,
                    self.pool.get(record['stage_model']).read(cr, 1, record['stage_id'], ['state'])['state']
                )[0] not in ('none', 'finish')
                for record in self.pool.get('process.site.stage').read(cr, 1, data['stage_ids'], ['stage_model', 'stage_id', 'stage'])
            ])
            if stage_list == set(['finish']) or stage_list == set(['finish', 'none']):
                access += 'p'

            val = False
            letter = name[6]
            #if letter in access or uid == 1:
            if letter in access:
                val = True

            res[data['id']] = val
        return res

    def _get_sub_state(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['stage_ids']):
            finish = False
            val = ''
            for stage in self.pool.get('process.site.stage').read(cr, uid, record['stage_ids'], ['stage_model', 'stage_id', 'stage']):
                process_str = get_state(STAGES, stage['stage'])[1]
                process = self.pool.get(stage['stage_model']).read(cr, 1, stage['stage_id'], ['state'])
                state = get_state(SUB_STATES, process['state'])[1]
                if process['state'] in ('work', 'in_approval', 'rectification', 'approved'):
                    val = '{process}: {state}'.format(process=process_str, state=state)
                if process['state'] == 'finish':
                    finish = True
                if val:
                    break
            if not val:
                if finish:
                    val = 'Все процессы завершены'
                else:
                    val = 'Процессы не начаты'
            res[record['id']] = val
        return res

    _columns = {
        'specialist_id': fields.many2one(
            'res.users',
            'Менеджер проекта',
            domain="[('groups_id','in',[45])]",
            required=False
        ),
        'state': fields.selection(STATES, 'Статус'),
        'history_ids': fields.one2many(
            'process.history',
            'process_id',
            'История',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'message_ids': fields.one2many(
            'process.messages',
            'process_id',
            'Переписка по проекту',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'access_ids': fields.one2many(
            'process.site.access',
            'process_id',
            'Доступы',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),
        'date_start': fields.date('Длительность проекта (с)', required=False),
        'date_end': fields.date('Длительность проекта (по)', required=False),
        'stage_ids': fields.one2many(
            'process.site.stage',
            'site_id',
            'Таблица Этапов',
            ondelete='CASCADE'
        ),
        #'signed_file_ids': fields.one2many(
        #    'ir.attachment',
        #    'res_id',
        #    'Подписанные файлы',
        #    domain=[
        #        (
        #            'res_model', 'in',
        #            [
        #                _name,
        #                'process.site.planning',
        #                'process.site.design',
        #                'process.site.makeup',
        #                'process.site.developing',
        #                'process.site.testing'
        #            ]
        #        ), ('tmp_res_model', '=', 'signed_file')],
        #    context={'res_model': _name, 'tmp_res_model': 'signed_file'}
        #),
        'signed_file_ids': fields.function(
            _get_attach,
            type='one2many',
            relation='ir.attachment',
            string='Пописанные файлы'
        ),

        'planning': fields.boolean('Проектирование', invisible=True),
        'design': fields.boolean('Дизайн', invisible=True),
        'makeup': fields.boolean('Верстка', invisible=True),
        'developing': fields.boolean('Программирование', invisible=True),
        'testing': fields.boolean('Тестирование', invisible=True),

        'planning_id': fields.one2many(
            'process.site.planning',
            'site_id',
            limit=1,
            string='Проектирование'
        ),
        'design_id': fields.one2many(
            'process.site.design',
            'site_id',
            limit=1,
            string='Дизайн'
        ),
        'makeup_id': fields.one2many(
            'process.site.makeup',
            'site_id',
            limit=1,
            string='Верстка'
        ),
        'developing_id': fields.one2many(
            'process.site.developing',
            'site_id',
            limit=1,
            string='Программирование'
        ),
        'testing_id': fields.one2many(
            'process.site.testing',
            'site_id',
            limit=1,
            string='Тестирование'
        ),
        'sub_state': fields.function(
            _get_sub_state,
            method=True,
            string='Статус процесса',
            type='char',
            size=200,
        ),
        'check_p': fields.function(
            _check_access,
            method=True,
            string='Проверка на завершение процессов',
            type='boolean',
            invisible=True
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на пм',
            type='boolean',
            invisible=True
        ),
    }

    def create(self, cr, user, vals, context=None):
        stage_pool = self.pool.get('process.site.stage')
        site_id = super(ProcessSite, self).create(cr, user, vals, context)

        for stage, title in STAGES:
            sub_process = 'process.site.{stage}'.format(stage=stage,)
            sub_process_id = self.pool.get(sub_process).create(cr, user, {'site_id': site_id}, context)
            stage_id = stage_pool.create(cr, user, {
                'stage_model': sub_process,
                'stage_id': sub_process_id,
                'stage': stage,
                'site_id': site_id})
            self.pool.get(sub_process).write(cr, user, [sub_process_id], {'stage_id': stage_id}, context)

        return site_id

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        error = ''
        for key in ['report_ids', 'message_ids']:
            for item in values.get(key, []):
                if item[0] == 0:
                    item[2]['process_model'] = self._name

        line_ids = []

        if values.get('specialist_id'):
            stage_ids = self.pool.get('process.site.stage').search(cr, uid, [('site_id', 'in', ids), ('manager_id', '=', False)])
            if stage_ids:
                self.pool.get('process.site.stage').write(cr, uid, stage_ids, {'manager_id': values['specialist_id']})

        for record in self.read(cr, uid, ids, ['state', 'stage_ids', 'specialist_id', 'date_start', 'date_end', 'launch_id']):
            next_state = values.get('state', False)
            state = record['state']

            if values.get('specialist_id'):
                line_ids += self.pool.get('process.launch')._get_pay_ids(cr, uid, record['launch_id'][0], '', {})[record['launch_id'][0]]['invoice_pay_ids']

            if next_state and next_state != state:
                if next_state == 'work':
                    if not values.get('specialist_id', False) and not record['specialist_id']:
                        error += 'Необходимо выбрать менеджера проекта'
                    if (not values.get('date_start', False) and not record['date_start']) or (not values.get('date_end', False) and not record['date_end']):
                        error += 'Необходимо выбрать продолжительность проекта'

                if error:
                    raise osv.except_osv("SITE", error)

                values.update({
                    'history_ids': [
                        (0, 0, {
                            'state': self.get_state(STATES, next_state)[1],
                            'process_model': self._name
                        })
                    ]})
        flag = super(ProcessSite, self).write(cr, uid, ids, values, context)
        if flag and line_ids and values.get('specialist_id'):
            self.pool.get('account.invoice.pay.line').write(cr, uid, line_ids, {'specialist_id': values['specialist_id']})
        return flag

ProcessSite()


class ProcessSiteBase(AbstractModel):
    _name = 'process.site.base'
    _description = u'Процессы - Site - Шаблон для субпроцессов'
    _rec_name = 'site_id'

    def _get_specialists(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, uid, ids, ['stage_id']):
            stage = self.pool.get('process.site.stage').read(cr, uid, record['stage_id'][0], ['specialist_ids'])
            specialists = [(4, i) for i in stage['specialist_ids']]
            res[record['id']] = specialists
        return res

    _columns = {
        'stage_id': fields.many2one('process.site.stage', 'Stage'),
        'site_id': fields.many2one('process.site', 'Проект', readonly=True),
        'partner_id': fields.related(
            'site_id',
            'partner_id',
            type='many2one',
            relation='res.partner',
            string='Партнер',
            readonly=True
        ),
        'service_id': fields.related(
            'site_id',
            'service_id',
            type='many2one',
            relation='brief.services.stage',
            string='Услуга',
            readonly=True
        ),
        'real_date_st': fields.related(
            'stage_id',
            'real_date_st',
            type='date',
            readonly=True,
            string='Реальная дата начала'
        ),
        'real_date_fn': fields.related(
            'stage_id',
            'real_date_fn',
            type='date',
            readonly=True,
            string='Реальная дата завершения'
        ),
        'plan_date_st': fields.related(
            'stage_id',
            'plan_date_st',
            type='date',
            readonly=True,
            string='Планируеммая дата начала'
        ),
        'plan_date_fn': fields.related(
            'stage_id',
            'plan_date_fn',
            type='date',
            readonly=True,
            string='Планируеммая дата завершения'
        ),
        'manager_id': fields.related(
            'stage_id',
            'manager_id',
            type='many2one',
            relation='res.users',
            readonly=True,
            string='Ответственный менеджер'
        ),
        'specialist_ids': fields.function(
            _get_specialists,
            method=True,
            string='Проверка на пм',
            type='one2many',
            relation='res.users'
        ),
    }

    def write(self, cr, user, ids, vals, context=None):
        for record in self.read(cr, user, ids, ['state', 'stage_id', 'approval_file_ids', 'signed_file_ids']):
            error = ''
            next_state = vals.get('state', False)
            state = record['state']
            if state == 'draft' and next_state == 'work':
                self.pool.get('process.site.stage').write(cr, user, [record['stage_id'][0]], {'real_date_st': dt.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")})

            if next_state == 'finish':
                self.pool.get('process.site.stage').write(cr, user, [record['stage_id'][0]], {'real_date_fn': dt.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")})

            if next_state and next_state != state:
                if next_state == 'in_approval':
                    if not vals.get('approval_file_ids', False) and not record['approval_file_ids']:
                        error += 'Необходимо добавить Файлы на утверждение'
                if next_state == 'finish':
                    if not vals.get('signed_file_ids', False) and not record['signed_file_ids']:
                        error += 'Необходимо добавить Подписанные файлы'

                if error:
                    raise osv.except_osv(get_state(STAGES, record['stage_id'][1])[1], error)

                self.pool.get('process.history').create(cr, user, {
                    'state': "{stage}: {state}".format(
                        stage=get_state(STAGES, record['stage_id'][1])[1],
                        state=get_state(SUB_STATES, next_state)[1]
                    ),
                    'process_model': 'process.site',
                    'process_id': record['id'],
                })
        return super(ProcessSiteBase, self).write(cr, user, ids, vals, context)
ProcessSiteBase()


class ProcessSiteStage(Model):
    _name = 'process.site.stage'
    _description = u'Процессы - Site - Этапы'
    _rec_name = 'stage'

    def _stage_state(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, 1, ids, ['stage_model', 'stage_id', 'stage']):
            res[record['id']] = False
            if record['stage_model'] and record['stage_id']:
                process = self.pool.get(record['stage_model']).read(cr, 1, record['stage_id'], ['state'])
                res[record['id']] = get_state(SUB_STATES, process['state'])[1]
            else:
                res[record['id']] = 'Отсутствует'
        return res

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['stage_model', 'stage_id', 'stage'], context):
            access = str()
            process = self.pool.get(data['stage_model']).read(cr, 1, data['stage_id'], ['state'])
            state = get_state(SUB_STATES, process['state'])[0]

            if state == 'none':
                access += 's'
            if state == 'draft':
                access += 'e'

            val = False
            letter = name[6]
            #if letter in access or uid == 1:
            if letter in access:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'stage': fields.selection(STAGES, 'Этап'),
        'plan_date_st': fields.date('Планируеммая дата начала'),
        'plan_date_fn': fields.date('Планируеммая дата завершения'),
        'real_date_st': fields.date('Реальная дата начала'),
        'real_date_fn': fields.date('Реальная дата завершения'),
        'manager_id': fields.many2one('res.users', 'Ответственный менеджер', domain="[('groups_id','in',[45])]",),
        'specialist_ids': fields.many2many(
            'res.users',
            'site_stage_specialist_rel',
            'specialist_id',
            'user_id',
            string='Ответственные специалисты',
            domain="[('groups_id','in',[45])]"
        ),
        'stage_state': fields.function(
            _stage_state,
            method=True,
            string='Статус процесса',
            type='char'
        ),
        'stage_model': fields.char('SubProcess Model', size=64, readonly=True, change_default=True),
        'stage_id': fields.integer('SubProcess ID', readonly=True),
        'site_id': fields.integer('Site ID', readonly=True),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на start',
            type='boolean',
            invisible=True
        ),
        'check_e': fields.function(
            _check_access,
            method=True,
            string='Проверка на end',
            type='boolean',
            invisible=True
        ),
    }

    def add_stage(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'view.process.site.stage.form'), ('model', '=', self._name)])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'name': 'Подключение услуги',
            'view_id': view_id,
            'res_id': ids[0] or 0,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': False,
            'context': {'add': True},
        }

    def save(self, cr, uid, ids, context=None):
        site_id = 0
        for record in self.read(cr, uid, ids, ['stage', 'stage_id', 'stage_model', 'site_id']):
            site_id = record['site_id']
            wf_service.trg_validate(uid, record['stage_model'], record['stage_id'], 'draft', cr)
            self.pool.get('process.site').write(cr, uid, [record['site_id']], {record['stage']: True})
        return {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'process.site',
            'name': 'Разработка и реализация стратегии site',
            'res_id': site_id,
            'type': 'ir.actions.act_window',
            'target': 'inline',
        }

    def off_stage(self, cr, uid, ids, context=None):
        site_id = 0
        for record in self.read(cr, uid, ids, ['stage', 'stage_id', 'stage_model', 'site_id']):
            site_id = record['site_id']
            stage_obj = self.pool.get(record['stage_model']).read(cr, uid, record['stage_id'], ['state'])
            if stage_obj['state'] in ('draft', 'none'):
                wf_service.trg_validate(uid, record['stage_model'], record['stage_id'], 'none', cr)
                self.write(cr, uid, [record['id']], {
                    'plan_date_st': False,
                    'plan_date_fn': False,
                    'real_date_st': False,
                    'real_date_fn': False,
                    'manager_id': False
                })
                self.pool.get('process.site').write(cr, uid, [record['site_id']], {record['stage']: False})
            else:
                raise osv.except_osv("SITE", "Нельзя отменить процесс по которому уже ведутся работы.")

        return {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'process.site',
            'name': 'Разработка и реализация стратегии site',
            'res_id': site_id,
            'type': 'ir.actions.act_window',
            'target': 'inline',
        }

    def _check_plan_start(self, cr, uid, ids, context=None):
        for self_obj in self.read(cr, 1, ids, ['plan_date_st', 'site_id'], context):
            if self.pool.get('process.site').search(cr, 1, [('id', '=', self_obj['site_id']), ('date_start', '>', self_obj['plan_date_st'])], context):
                return False
            return True

    def _check_plan_end(self, cr, uid, ids, context=None):
        for self_obj in self.read(cr, 1, ids, ['plan_date_fn', 'site_id'], context):
            if self.pool.get('process.site').search(cr, 1, [('id', '=', self_obj['site_id']), ('date_end', '<', self_obj['plan_date_fn'])], context):
                return False
            return True

    _constraints = [
        (
            _check_plan_start,
            'не может быть раньше начала работы по проекту!',
            [u'Планируеммая дата начала']
        ),
        (
            _check_plan_end,
            'не может быть позже завершения работ по проекту!',
            [u'Планируеммая дата завершения']
        ),
    ]
ProcessSiteStage()


class ProcessSitePlanning(Model):
    _name = 'process.site.planning'
    _inherit = 'process.site.base'
    _description = u'Процессы - Site - Проектирование'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['stage_id', 'site_id'], context):
            access = str()

            stage = self.pool.get('process.site.stage').read(cr, uid, data['stage_id'][0], ['manager_id'])
            if stage.get('manager_id') and stage['manager_id'][0] == uid:
                access += 's'

            site = self.pool.get('process.site').read(cr, uid, data['site_id'][0], ['responsible_id'])
            if site.get('responsible_id') and site['responsible_id'][0] == uid:
                access += 'r'

            val = False
            letter = name[6]
            #if letter in access or uid == 1:
            if letter in access:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'approval_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Файлы на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'approval_file')],
            context={'res_model': _name, 'tmp_res_model': 'approval_file'}
        ),
        'comment_ids': fields.one2many(
            'process.site.comments',
            'process_id',
            'Комментарии',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),
        'signed_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Подписанные файлы',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'signed_file')],
            context={'res_model': _name, 'tmp_res_model': 'signed_file'}
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на пм',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Проверка на менеджера по работе',
            type='boolean',
            invisible=True
        ),
        'state': fields.selection(PLANNING_STATES, 'Статус'),
    }

    _defaults = {
        'state': 'none',
    }
ProcessSitePlanning()


class ProcessSiteDesign(Model):
    _name = 'process.site.design'
    _inherit = 'process.site.base'
    _description = u'Процессы - Site - Дизайн'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['stage_id', 'site_id'], context):
            access = str()

            stage = self.pool.get('process.site.stage').read(cr, uid, data['stage_id'][0], ['manager_id'])
            if stage.get('manager_id') and stage['manager_id'][0] == uid:
                access += 's'

            site = self.pool.get('process.site').read(cr, uid, data['site_id'][0], ['responsible_id'])
            if site.get('responsible_id') and site['responsible_id'][0] == uid:
                access += 'r'

            val = False
            letter = name[6]
            #if letter in access or uid == 1:
            if letter in access:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'approval_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Файлы на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'approval_file')],
            context={'res_model': _name, 'tmp_res_model': 'approval_file'}
        ),
        'comment_ids': fields.one2many(
            'process.site.comments',
            'process_id',
            'Комментарии',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),
        'signed_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Подписанные файлы',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'signed_file')],
            context={'res_model': _name, 'tmp_res_model': 'signed_file'}
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на пм',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Проверка на менеджера по работе',
            type='boolean',
            invisible=True
        ),
        'state': fields.selection(DESIGN_STATES, 'Статус'),
    }

    _defaults = {
        'state': 'none',
    }
ProcessSiteDesign()


class ProcessSiteMakeup(Model):
    _name = 'process.site.makeup'
    _inherit = 'process.site.base'
    _description = u'Процессы - Site - Верстка'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['stage_id', 'site_id'], context):
            access = str()

            stage = self.pool.get('process.site.stage').read(cr, uid, data['stage_id'][0], ['manager_id'])
            if stage.get('manager_id') and stage['manager_id'][0] == uid:
                access += 's'

            site = self.pool.get('process.site').read(cr, uid, data['site_id'][0], ['responsible_id'])
            if site.get('responsible_id') and site['responsible_id'][0] == uid:
                access += 'r'

            val = False
            letter = name[6]
            #if letter in access or uid == 1:
            if letter in access:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'approval_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Файлы на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'approval_file')],
            context={'res_model': _name, 'tmp_res_model': 'approval_file'}
        ),
        'comment_ids': fields.one2many(
            'process.site.comments',
            'process_id',
            'Комментарии',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),
        'signed_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Подписанные файлы',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'signed_file')],
            context={'res_model': _name, 'tmp_res_model': 'signed_file'}
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на пм',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Проверка на менеджера по работе',
            type='boolean',
            invisible=True
        ),
        'state': fields.selection(MAKEUP_STATES, 'Статус'),
    }

    _defaults = {
        'state': 'none',
    }
ProcessSiteMakeup()


class ProcessSiteDeveloping(Model):
    _name = 'process.site.developing'
    _inherit = 'process.site.base'
    _description = u'Процессы - Site - Программирование'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['stage_id', 'site_id'], context):
            access = str()

            stage = self.pool.get('process.site.stage').read(cr, uid, data['stage_id'][0], ['manager_id'])
            if stage.get('manager_id') and stage['manager_id'][0] == uid:
                access += 's'

            site = self.pool.get('process.site').read(cr, uid, data['site_id'][0], ['responsible_id'])
            if site.get('responsible_id') and site['responsible_id'][0] == uid:
                access += 'r'

            val = False
            letter = name[6]
            #if letter in access or uid == 1:
            if letter in access:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'approval_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Файлы на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'approval_file')],
            context={'res_model': _name, 'tmp_res_model': 'approval_file'}
        ),
        'comment_ids': fields.one2many(
            'process.site.comments',
            'process_id',
            'Комментарии',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),
        'signed_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Подписанные файлы',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'signed_file')],
            context={'res_model': _name, 'tmp_res_model': 'signed_file'}
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на пм',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Проверка на менеджера по работе',
            type='boolean',
            invisible=True
        ),
        'state': fields.selection(DEVELOPING_STATES, 'Статус'),
    }

    _defaults = {
        'state': 'none',
    }
ProcessSiteDeveloping()


class ProcessSiteTesting(Model):
    _name = 'process.site.testing'
    _inherit = 'process.site.base'
    _description = u'Процессы - Site - Тестирование'

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['stage_id', 'site_id'], context):
            access = str()

            stage = self.pool.get('process.site.stage').read(cr, uid, data['stage_id'][0], ['manager_id'])
            if stage.get('manager_id') and stage['manager_id'][0] == uid:
                access += 's'

            site = self.pool.get('process.site').read(cr, uid, data['site_id'][0], ['responsible_id'])
            if site.get('responsible_id') and site['responsible_id'][0] == uid:
                access += 'r'

            val = False
            letter = name[6]
            #if letter in access or uid == 1:
            if letter in access:
                val = True

            res[data['id']] = val
        return res

    _columns = {
        'approval_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Файлы на утверждение',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'approval_file')],
            context={'res_model': _name, 'tmp_res_model': 'approval_file'}
        ),
        'comment_ids': fields.one2many(
            'process.site.comments',
            'process_id',
            'Комментарии',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}
        ),
        'signed_file_ids': fields.one2many(
            'ir.attachment',
            'res_id',
            'Подписанные файлы',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'signed_file')],
            context={'res_model': _name, 'tmp_res_model': 'signed_file'}
        ),
        'check_s': fields.function(
            _check_access,
            method=True,
            string='Проверка на пм',
            type='boolean',
            invisible=True
        ),
        'check_r': fields.function(
            _check_access,
            method=True,
            string='Проверка на менеджера по работе',
            type='boolean',
            invisible=True
        ),
        'state': fields.selection(TESTING_STATES, 'Статус'),
    }

    _defaults = {
        'state': 'none',
    }
ProcessSiteTesting()


class ProcessSiteComments(Model):
    _name = 'process.site.comments'
    _inherit = 'process.base.staff'
    _description = u'Процессы - Site - Комментарии'
ProcessSiteComments()


class ProcessSiteAccess(Model):
    _name = 'process.site.access'
    _inherit = 'process.base.staff'
    _description = u'Процессы - Site - Доступы'

    _columns = {
        'name': fields.char('URL', size=250),
        'login': fields.char('Логин', size=250),
        'passwd': fields.char('Пароль', size=250),
    }
ProcessSiteAccess()