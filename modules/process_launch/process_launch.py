# coding=utf-8
__author__ = 'andrey'
import netsvc
from openerp.osv import fields, osv
from openerp.osv.orm import Model, AbstractModel
from notify import notify


STATES = (
    ('draft', 'Черновик'),
    ('revision', 'Доработка'),
    ('agreement', 'Согласование'),
    ('in_process', 'В работе'),
    ('finish', 'Завершен'),
    ('cancel', 'Отменен'),
)
wf_service = netsvc.LocalService("workflow")


class ProcessLaunch(Model):
    _name = 'process.launch'
    _description = u'Process - Единая карточка запуска процесса'
    _order = 'create_date desc'

    @staticmethod
    def get_state(states, state):
        return [item for item in states if item[0] == state][0]

    def _check_access(self, cr, uid, ids, name, arg, context=None):
        """
            Динамически определяет роли на форме
        """
        res = {}
        for data in self.read(cr, uid, ids, ['user_id'], context):
            access = str()

            #  Автор
            if data.get('user_id') and data['user_id'][0] == uid:
                access += 'a'

            #  Бекетова Катя
            if uid == 14:
                access += 'm'

            val = False
            letter = name[6]
            if letter in access or uid == 1:
                val = True

            res[data['id']] = val
        return res

    def _attach(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for data in self.read(cr, uid, ids, ['service_id', 'partner_id'], context):
            attach = []
            brief_ids = self.pool.get('brief.main').search(cr, 1, [('services_ids', '=', data['service_id'][0]), ('partner_id', '=', data['partner_id'][0])])
            for record in self.pool.get('brief.main').read(cr, 1, brief_ids, ['rep_file_id']):
                attach.extend([(0, 0, {'name': i.name, 'file': i.file, 'object': 'process.launch', 'user_id': i.user_id.id})
                               for i in self.pool.get('attach.files').browse(cr, 1, record['rep_file_id'])])
            res[data['id']] = attach
        return res

    def _process_state(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.read(cr, 1, ids, ['process_model', 'process_id', 'direction']):
            res[record['id']] = False
            if record['process_model'] and record['process_id']:
                process = self.pool.get(record['process_model']).read(cr, 1, record['process_id'], ['state'])
                module = __import__(record['process_model'].replace('.', '_'))

                states = getattr(getattr(module, record['direction'].lower()), 'STATES')
                try:
                    res[record['id']] = self.get_state(states, process['state'])[1]
                except:
                    res[record['id']] = False
        return res

    def _get_pay_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for data in self.read(cr, uid, ids, ['service_id', 'account_ids'], context):
            value = {
                'price': 0,
                'price_ye': 0,
                'paid': 0,
                'invoice_pay_ids': []
            }
            service_id = 0
            account_ids = 0
            if data['service_id']:
                service_id = data['service_id'][0]
            if data['account_ids']:
                account_ids = data['account_ids']
            if service_id and account_ids:
                value['price'], value['price_ye'], value['paid'], value['invoice_pay_ids'] = self._get_account_info(cr, 1, account_ids, service_id)

            res[data['id']] = value
        return res

    def _get_head(self, cr, user, leader_group_id):
        users = self.pool.get('res.users').search(cr, user, [('groups_id', 'in', leader_group_id)], order='id')
        if users:
            u = [x for x in users if x not in [1, 5, 13, 18, 354, 472]]
            if u:
                return u[0]

    def _get_service_info(self, cr, uid, service_id):
        service = self.pool.get('brief.services.stage').read(cr, uid, [service_id], ['direction', 'leader_group_id'])
        return service[0]['direction'], self._get_head(cr, uid, service[0]['leader_group_id'][0])

    def _get_account_info(self, cr, uid, account_ids, service_id):
        line_ids = self.pool.get('account.invoice.line').search(
            cr,
            uid,
            [
                ('invoice_id', 'in', account_ids),
                ('service_id', '=', service_id)
            ])
        if line_ids:
            invoice_lines = self.pool.get('account.invoice.line').read(cr, uid, line_ids,
                                                                       ['price_currency', 'price_unit', 'paid'])
            price_currency = 0
            price_unit = 0
            paid = 0
            for line in invoice_lines:
                price_currency += line['price_currency']
                price_unit += line['price_unit']
                paid += line['paid']
            pay_line_ids = self.pool.get('account.invoice.pay.line').search(cr, uid, [('invoice_id', 'in', account_ids)])

            return price_currency, price_unit, paid, pay_line_ids

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        domain = []
        service_domain = []
        if partner_id:
            domain = [('partner_id', '=', partner_id)]
            added_ids = self.pool.get('partner.added.services').search(cr, 1, [('partner_id', '=', partner_id)])
            services = self.pool.get('partner.added.services').read(cr, 1, added_ids, ['service_id'])
            service_domain = [item['service_id'][0] for item in services if item['service_id']]

        return {'domain': {'service_id': [('id', 'in', service_domain)], 'contract_id': domain,
                           'account_ids': domain + [('type', '=', 'out_invoice')]}}

    def onchange_service_id(self, cr, uid, ids, partner_id, service_id, context=None):
        domain = []
        invoice_ids = []
        attach = []

        if partner_id:
            domain.append(('partner_id.id', '=', partner_id))
            invoice_ids = self.pool.get('account.invoice').search(cr, 1, [('partner_id', '=', partner_id),
                                                                          ('type', '=', 'out_invoice')])
        if service_id and invoice_ids:
            invoice_line_ids = self.pool.get('account.invoice.line').search(cr, 1, [('invoice_id', 'in', invoice_ids),
                                                                                    ('service_id', '=', service_id)])
            invoice_lines = self.pool.get('account.invoice.line').read(cr, 1, invoice_line_ids, ['invoice_id'])
            domain.append(('service_id', '=', service_id))
            invoice_ids = [r['invoice_id'][0] for r in invoice_lines if r['invoice_id']]

            brief_ids = self.pool.get('brief.main').search(cr, 1, [('services_ids', '=', service_id), ('partner_id', '=', partner_id)])

            for record in self.pool.get('brief.main').read(cr, 1, brief_ids, ['rep_file_id']):
                attach.extend([(0, 0, {'name': i.name, 'file': i.file, 'object': i.object, 'user_id': i.user_id.id})
                               for i in self.pool.get('attach.files').browse(cr, 1, record['rep_file_id'])])

        direction, service_head_id = self._get_service_info(cr, 1, service_id)
        return {
            'domain': {
                'contract_id': domain,
                'account_ids': [('id', 'in', invoice_ids), ('type', '=', 'out_invoice')]
            },
            'value': {
                'direction': direction,
                'service_head_id': service_head_id,
                'rep_file_id': attach
            }
        }

    def onchange_account_ids(self, cr, uid, ids, account_ids, service_id, context=None):
        value = {
            'price': False,
            'price_ye': False,
            'paid': False,
            'invoice_pay_ids': False
        }
        if account_ids and service_id:
            account_ids = [y for i in account_ids for y in i[2]]
            value_ids = self.pool.get('account.invoice.line').search(
                cr,
                1,
                [
                    ('invoice_id', 'in', account_ids),
                    ('service_id', '=', service_id)
                ])
            if value_ids:
                price, price_ye, paid, line_ids = self._get_account_info(cr, 1, account_ids, service_id)
                value = {
                    'price': price,
                    'price_ye': price_ye,
                    'paid': paid,
                    'invoice_pay_ids': line_ids
                }
        return {'value': value}

    def onchange_contract_id(self, cr, uid, ids, contract_id, context=None):
        contract = self.pool.get('brief.contract').read(cr, 1, [contract_id], ['contract_approved_file'])
        if contract and contract[0]['contract_approved_file']:
            return {
                'value': {
                    'contract_file': contract[0]['contract_approved_file'][0]
                }
            }
        return {'value': {'contract_file': False}}

    _columns = {
        'name': fields.char('Наименование процесса', size=250),
        'create_date': fields.datetime('Дата создания', select=True),
        'partner_id': fields.many2one(
            'res.partner',
            'Партнер',
            readonly=True,
            required=True,
            states={
                'draft': [('readonly', False)],
                'revision': [('readonly', False)],
            }, ),
        'user_id': fields.many2one(
            'res.users',
            'Автор',
            readonly=True
        ),
        'responsible_id': fields.many2one(
            'res.users',
            'Менеджер',
            readonly=True
        ),
        'service_id': fields.many2one(
            'brief.services.stage',
            'Услуга',
            readonly=True,
            required=True,
            states={
                'draft': [('readonly', False)],
                'revision': [('readonly', False)],
            }
        ),
        'contract_id': fields.many2one(
            'brief.contract',
            'Договор',
            readonly=True,
            required=False,
            states={
                'draft': [('readonly', False)],
                'revision': [('readonly', False)],
            },
            domain="[('partner_id', '=', partner_id)]"
        ),
        'contract_file': fields.related(
            'contract_id',
            'contract_approved_file',
            type='many2one',
            relation='attach.files',
            string='Файл утвержденого договора',
            readonly=True
        ),
        'contract_file_id': fields.many2one(
            'ir.attachment',
            'Файл договора',
            readonly=True,
            required=False,
            states={
                'draft': [('readonly', False)],
                'revision': [('readonly', False)],
            },
            domain="['|', '&', ('res_model', '=', 'process.launch'), ('tmp_res_model', '=', 'contract_file'), '&', ('res_model', '=', 'res.partner'), ('res_id', '=', partner_id)]",
            context="{'res_model': 'res.partner', 'res_id': partner_id}"
        ),
        'account_ids': fields.many2many(
            'account.invoice',
            'account_invoice_launch_rel',
            'launch_id',
            'invoice_id',
            'Счет',
            readonly=False,
            domain="[('partner_id', '=', partner_id), ('invoice_line.service_id', 'in', [service_id]), ('type', '=', 'out_invoice')]",),
        'account_file_id': fields.many2one(
            'ir.attachment',
            'Файл платежного поручения',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'account_file')],
            context={'res_model': _name, 'tmp_res_model': 'account_file'},
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'revision': [('readonly', False)],
            }
        ),
        'pay_date': fields.datetime(
            'Дата платежного поручения',
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'revision': [('readonly', False)],
            }),
        'price': fields.function(
            _get_pay_ids,
            method=True,
            type='float',
            digits=(10, 6),
            string='Стоимость в валюте счета',
            readonly=True,
            multi='account'
        ),
        'price_ye': fields.function(
            _get_pay_ids,
            method=True,
            type='float',
            digits=(10, 6),
            string='Стоимость в $',
            readonly=True,
            multi='account'
        ),
        'paid': fields.function(
            _get_pay_ids,
            method=True,
            type='float',
            digits=(10, 6),
            string='Оплачено',
            readonly=True,
            multi='account'
        ),
        'invoice_pay_ids': fields.function(
            _get_pay_ids,
            method=True,
            string='Платежи',
            type='one2many',
            relation='account.invoice.pay.line',
            readonly=True,
            multi='account'
        ),

        'direction': fields.related(
            'service_id',
            'direction',
            type='char',
            size=50,
            string='Направление'
        ),
        'service_head_id': fields.many2one(
            'res.users',
            'Руководитель направления',
            readonly=True,
            help='Руководитель направления по которому составлен договор.'),
        'state': fields.selection(STATES, 'Статус', readonly=True),
        'check_a': fields.function(
            _check_access,
            method=True,
            string='Проверка на автора',
            type='boolean',
            invisible=True
        ),
        'check_m': fields.function(
            _check_access,
            method=True,
            string='Проверка на Бекетову Катю',
            type='boolean',
            invisible=True
        ),

        'comment': fields.text(
            'Комментарий по доработке',
            readonly=True,
            states={
                'agreement': [('readonly', False)]
            }
        ),
        'rep_file_id': fields.function(
            _attach,
            relation='attach.files',
            type="one2many",
            string='Медиаплан/коммерческое предложение',
            domain=[('object', '=', 'process.launch')],
            method=True,
            store=False,
            readonly=True),

        'process_model': fields.char('Process Model', size=64, readonly=True, change_default=True),
        'process_id': fields.integer('Process ID', readonly=True),
        'history_ids': fields.one2many(
            'process.history',
            'process_id',
            'История',
            domain=[('process_model', '=', _name)],
            context={'process_model': _name}),
        'process_state': fields.function(
            _process_state,
            method=True,
            string='Статус процесса',
            type='char'
        ),



        # SMM
        'targeted_advertising': fields.boolean(
            'Таргетированная реклама',
            states={
                'in_process': [('readonly', True)],
                'finish': [('readonly', True)],
            }),
        'lead_management': fields.boolean(
            'Лид менеджмент',
            states={
                'in_process': [('readonly', True)],
                'finish': [('readonly', True)],
            }),
        'hidden_marketing': fields.boolean(
            'Скрытый маркетинг',
            states={
                'in_process': [('readonly', True)],
                'finish': [('readonly', True)],
            }),
        'reputation_management': fields.boolean(
            'Продвижение в соц. сетях',
            states={
                'in_process': [('readonly', True)],
                'finish': [('readonly', True)],
            }),
        'date_partners_from': fields.date(
            'с',
            states={
                'in_process': [('readonly', True)],
                'finish': [('readonly', True)],
            }),
        'date_partners_to': fields.date(
            'по',
            states={
                'in_process': [('readonly', True)],
                'finish': [('readonly', True)],
            }),

        'call_type': fields.selection(
            (
                ('in', 'Входящая кампания'),
                ('out', 'Исходящая кампания'),
            ), 'Тип кампании',
            states={
                'in_process': [('readonly', True)],
                'finish': [('readonly', True)],
            }
        )
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'responsible_id': lambda self, cr, uid, context: uid,
        'partner_id': lambda self, cr, uid, context: context.get('partner_id', False),
        'state': 'draft',
        'check_a': True,
        'call_type': 'in'
    }

    def create(self, cr, user, vals, context=None):
        account_id = vals.get('account_id', 0)
        service_id = vals.get('service_id', 0)
        if service_id:
            vals['direction'], vals['service_head_id'] = self._get_service_info(cr, 1, service_id)
            if account_id:
                vals['price'], vals['price_ye'], vals['paid'], line_ids = \
                    self._get_account_info(cr, 1, account_id, service_id)
        return super(ProcessLaunch, self).create(cr, user, vals, context)

    @notify.msg_send(_name)
    def write(self, cr, uid, ids, values, context=None):
        error = ''
        for record in self.read(cr, uid, ids, ['state', 'comment', 'account_file_id', 'account_ids', 'contract_file_id', 'contract_id']):
            next_state = values.get('state', False)
            state = record['state']

            if next_state and next_state != state:
                if next_state == 'revision' and (not values.get('comment', False) and not record['comment']):
                    error += 'Необходимо ввести комментарий по доработке'
                if next_state == 'agreement':
                    if not values.get('account_file_id', False) and not record['account_file_id'] and not values.get('account_ids', False) and not record['account_ids']:
                        error += 'Необходимо выбрать счет или прикрепить платежное поручение'

                    if not values.get('contract_file_id', False) and not record.get('contract_file_id') and not values.get('contract_id', False) and not record.get('contract_id'):
                        error += 'Необходимо выбрать договор или прикрепить файл договора'

                if error:
                    raise osv.except_osv("Единая карточка запуска", error)

                values.update({'history_ids': [(0, 0, {'state': self.get_state(STATES, next_state)[1], 'process_model': self._name})]})
        return super(ProcessLaunch, self).write(cr, uid, ids, values, context)

    def get_process_val(self, cr, user, ids):
        val = {}
        for record in self.read(cr, user, ids, ['direction', 'call_type']):
            process_model = 'process.{direction}'.format(direction=record['direction'].lower())
            if record['direction'] == 'CALL':
                process_model += '.{type}'.format(type=record['call_type'])
            try:
                process_id = self.pool.get(process_model).create(cr, user, {'launch_id': record['id']})
                val = {'process_id': process_id, 'process_model': process_model}
            except AttributeError:
                pass
        return val

    def process_start(self, cr, user, ids):
        vals = {'state': 'in_process'}
        vals.update(self.get_process_val(cr, user, ids))
        return self.write(cr, user, ids, vals)

    def process_create(self, cr, user, ids, context=None):
        return self.write(cr, user, ids, self.get_process_val(cr, user, ids))

    def process_add(self, cr, user, ids):
        flag = True
        for record in self.read(cr, user, ids, ['partner_id', 'service_id']):
            as_ids = self.pool.get('partner.added.services').search(cr, user, [('partner_id', '=', record['partner_id'][0]), ('service_id', '=', record['service_id'][0])])
            if as_ids:
                flag = self.pool.get('partner.added.services').write(cr, user, as_ids, {'check': True})
        return flag
ProcessLaunch()


class ProcessBase(AbstractModel):
    _name = 'process.base'
    _order = 'create_date desc'

    @staticmethod
    def get_state(states, state):
        return [item for item in states if item[0] == state][0]

    def name_get(self, cr, user, ids, context=None):
        return [
            (
                r['id'],
                "{0}".format(r['partner_id'][1].encode('utf8'),)
            ) for r in self.read(cr, user, ids, ['partner_id', 'service_id'])]

    _columns = {
        'launch_id': fields.many2one('process.launch', 'Карточка запуска'),
        'create_date': fields.datetime('Дата создания', select=True),

        'partner_id': fields.related(
            'launch_id',
            'partner_id',
            relation='res.partner',
            type='many2one',
            string='Партнер',
            store=False
        ),
        'service_id': fields.related(
            'launch_id',
            'service_id',
            relation='brief.services.stage',
            type='many2one',
            string='Услуга',
            store=False
        ),
        'user_id': fields.related(
            'launch_id',
            'user_id',
            relation='res.users',
            type='many2one',
            string='Автор',
            store=True
        ),
        'responsible_id': fields.related(
            'launch_id',
            'responsible_id',
            relation='res.users',
            type='many2one',
            string='Менеджер',
            store=True
        ),

        'contract_id': fields.related(
            'launch_id',
            'contract_id',
            relation='brief.contract',
            type='many2one',
            string='Договор',
            domain="[('partner_id', '=', partner_id)]",
            store=False
        ),
        'contract_file': fields.related(
            'launch_id',
            'contract_file',
            type='many2one',
            relation='attach.files',
            string='Файл утвержденого договора'
        ),
        'account_ids': fields.related(
            'launch_id',
            'account_ids',
            relation='account.invoice',
            type='many2many',
            domain="[('partner_id', '=', partner_id), ('invoice_line.service_id', 'in', [service_id]), ('type', '=', 'out_invoice')]",
            string='Счет',
            readonly=True),
        'account_file_id': fields.related(
            'launch_id',
            'account_file_id',
            relation='ir.attachment',
            type='many2one',
            readonly=True,
            string='Файл платежного поручения'),
        'account_date': fields.related(
            'launch_id',
            'pay_date',
            type='datetime',
            readonly=True,
            string='Дата платежного поручения'),
        'price': fields.related(
            'launch_id',
            'price',
            type='float',
            digits=(10, 6),
            string='Стоимость в валюте счета'
        ),
        'price_ye': fields.related(
            'launch_id',
            'price_ye',
            type='float',
            digits=(10, 6),
            string='Стоимость в $'
        ),
        'paid': fields.related(
            'launch_id',
            'paid',
            type='float',
            digits=(10, 6),
            string='Оплачено'
        ),
        'invoice_pay_ids': fields.related(
            'launch_id',
            'invoice_pay_ids',
            type='one2many',
            relation='account.invoice.pay.line',
            string='Платежи',
            readonly=True
        ),
        'direction': fields.related(
            'launch_id',
            'direction',
            type='char',
            size=50,
            string='Направление'
        ),
        'service_head_id': fields.related(
            'launch_id',
            'service_head_id',
            relation='res.users',
            type='many2one',
            string='Руководитель направления'),

        'site_url': fields.char('Сайт', size=255),
    }

    def close_launch(self, cr, uid, ids):
        for record in self.read(cr, 1, ids, ['launch_id']):
            wf_service.trg_validate(uid, 'process.launch', record['launch_id'][0], 'finish', cr)

    def cancel_launch(self, cr, uid, ids):
        for record in self.read(cr, 1, ids, ['launch_id']):
            wf_service.trg_validate(uid, 'process.launch', record['launch_id'][0], 'finish', cr)

    def update_partner(self, cr, uid, ids):
        for record in self.read(cr, 1, ids, ['partner_id', 'specialist_id']):
            if record.get('specialist_id'):
                employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', record['specialist_id'][0])])
                for employee in self.pool.get('hr.employee').read(cr, uid, employee_ids, ['department_id']):
                    if employee.get('department_id'):
                        if not self.pool.get('partner.operational.departments').search(cr, uid, [('department', '=', employee['department_id'][0]), ('specialist', '=', employee['id']), ('partner_id', '=', record['partner_id'][0])]):
                            self.pool.get('partner.operational.departments').create(cr, uid, {'department': employee['department_id'][0], 'specialist': employee['id'], 'partner_id': record['partner_id'][0]})


class ProcessHistory(Model):
    _name = 'process.history'
    _description = u'Процессы - История переходов'
    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'state': fields.char('На этап', size=65),
        'process_id': fields.integer('Process ID', readonly=True),
        'process_model': fields.char('Process Model', size=64, readonly=True, change_default=True),
    }

    _defaults = {
        'process_model': lambda cr, u, i, ctx: ctx.get('process_model'),
    }

    _order = "create_date desc"
ProcessHistory()


class ProcessBaseStaff(AbstractModel):
    _name = 'process.base.staff'
    _columns = {
        'create_uid': fields.many2one('res.users', 'Перевел', readonly=True),
        'create_date': fields.datetime('Дата создания', readonly=True),
        'name': fields.text('Комментарий'),
        'process_id': fields.integer('Process ID', readonly=True),
        'process_model': fields.char('Process Model', size=64, readonly=True, change_default=True),
    }

    _defaults = {
        'process_model': lambda cr, u, i, ctx: ctx.get('process_model'),
    }

    _order = "create_date desc"


class ProcessMessages(Model):
    _name = 'process.messages'
    _inherit = 'process.base.staff'
    _description = u'Процессы - Сообщения'

    _columns = {
        'attachment_id': fields.many2one(
            'ir.attachment',
            'Прикрепленный файл',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'message')],
            context={'res_model': _name, 'tmp_res_model': 'message'}
        ),
    }
ProcessMessages()


class ProcessReports(Model):
    _name = 'process.reports'
    _inherit = 'process.base.staff'
    _description = u'Процессы - Отчеты'

    _columns = {
        'attachment_id': fields.many2one(
            'ir.attachment',
            'Прикрепленный файл',
            domain=[('res_model', '=', _name), ('tmp_res_model', '=', 'reports')],
            context={'res_model': _name, 'tmp_res_model': 'reports'}),
    }
ProcessReports()


class ProcessIndicators(Model):
    _name = 'process.sla.indicators'
    _inherit = 'kpi.indicators.reference'
    _description = u'Ключевые показатели SLA'

    _columns = {
        'type': fields.selection(
            (
                ('video', 'video'),
                ('call', 'call'),
                ('smm', 'smm'),
                ('seo', 'seo'),
                ('ppc', 'ppc'),
            ), "Тип показателя", required=True
        ),
    }
ProcessIndicators()


class ProcessSla(Model):
    _name = 'process.sla'
    _inherit = 'process.base.staff'
    _order = 'period_name desc'
    _description = u'Процессы - SLA'

    _columns = {
        'type': fields.char('Тип показателя', size=10, invisible=True),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')]),
        'period_name': fields.related(
            'period_id',
            'name',
            type='char',
            size=7,
            store=True
        ),
        'line_ids': fields.one2many('process.sla.line', 'sla_id', 'Показатели'),
        'avg_mbo': fields.float('MBO', digits=(10, 2)),
    }

    _defaults = {
        'type': lambda cr, u, i, ctx: ctx.get('type', 'call').lower(),
    }

    def change_sla(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', 'like', 'SLA'), ('model', '=', self._name)])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'name': 'SLA',
            'view_id': view_id,
            'res_id': context.get('sla_id', 0),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        }

    def save(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
ProcessSla()


class ProcessSlaLine(Model):
    _name = 'process.sla.line'
    _description = u'Процессы - SLA - показатели'

    def _calculate(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for row in self.browse(cr, uid, ids, context):
            plan, fact, weight = row.plan, row.fact, row.weight
            try:
                result = 0
                for formula in row.name.formula.split(';'):
                    exec compile(formula, '<string>', 'exec')
                if not row.name.index_type and result > 100:
                    result = 100
                result = round(result, 2)

            except ZeroDivisionError:
                result = 0

            res[row.id] = {
                'percentage': result,
                'mbo': round((row.weight * result), 2) if result else 0,
            }
        return res

    _columns = {
        'name': fields.many2one(
            'process.sla.indicators',
            'Показатель',
            required=True,
        ),
        'sla_id': fields.many2one('process.sla', 'SLA'),

        'plan': fields.float('План'),
        'fact': fields.float('Факт'),
        'units': fields.related(
            'name',
            'units',
            type="char",
            string="Единицы измерения",
            readonly=True
        ),
        'weight': fields.float('Вес'),
        'previous_period': fields.float('Предыдущий период', readonly=True),
        'percentage': fields.function(
            _calculate,
            method=True,
            string="Процент выполнения",
            type="float",
            multi='base'
        ),
        'mbo': fields.function(
            _calculate,
            method=True,
            string="MBO",
            type="float",
            multi='base'),
        'type': fields.char('Тип показателя', size=10, invisible=True),
    }

    _defaults = {
        'type': lambda cr, u, i, ctx: ctx.get('type', 'call').lower()
    }
ProcessSlaLine()


class ProcessCosts(Model):
    _name = 'process.costs'
    _inherit = 'process.base.staff'
    _description = u'Процессы - Затраты на партнера'
    _order = 'period_name desc'

    _columns = {
        'name': fields.float('Сумма'),
        'type': fields.selection(
            (
                ('href', 'Cсылки'),
                ('copyright', 'Копирайтинг'),
                ('tech', 'Техподдержка'),
            ),
            string='Тип затрат', required=True
        ),
        'period_id': fields.many2one('kpi.period', 'Период', domain=[('calendar', '=', 'rus')], required=True),
        'period_name': fields.related(
            'period_id',
            'name',
            type='char',
            size=7,
            store=True
        ),
    }
ProcessCosts()

