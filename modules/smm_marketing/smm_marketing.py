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
import tools
from tools.translate import _

class smm_socialnet_stage(osv.osv):
    _name = "smm.socialnet.stage"
    _description = "Справочник социальных сетей"
    _order = 'name'
    _columns = {
       'name':fields.char('Название социальной сети', size=255, required=True, select=True),
    }
smm_socialnet_stage()

class smm_socialnet_right_stage(osv.osv):
    _name = "smm.socialnet.right.stage"
    _description = "Справочник прав социальных сетей"
    _order = 'name'
    _columns = {
       'name':fields.char('Тип', size=125, required=True, select=True),
    }
smm_socialnet_right_stage()

class smm_socialnet(osv.osv):
    _name = "smm.socialnet"
    _description = "Социальные сети"
    _order = 'cr_date'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'name_id':fields.many2one('smm.socialnet.stage', 'Социальная сеть', select=True),
        'cr_date':fields.date('Дата создания', select=True),
        'name_person':fields.char('Имя персонажа', size=255),
        'login':fields.char('Логин', size=64),
        'password':fields.char('Пароль', size=64),
        'telephone':fields.char('Привязка №тел.', size=125),
        'rights_id':fields.many2one('smm.socialnet.right.stage', 'Права', select=True),
        'partner_id':fields.many2one('res.partner', 'Компания', select=True),
        'url_person':fields.char('URL персонажа', size=255),
        'email':fields.char('Эл. почта', size=255),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_socialnet_rel', 'smm_soc_id', 'usr_id', string='Ответственный', select=True),
    }
    _defaults = {
        'cr_date':time.strftime('%Y-%m-%d'),
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
smm_socialnet()

class smm_fotohost_stage(osv.osv):
    _name = "smm.fotohost.stage"
    _description = "Справочник фото хостинга"
    _order = 'name'
    _columns = {
       'name':fields.char('Название фото хостинга', size=255, required=True, select=True),
    }
smm_fotohost_stage()

class smm_fotohost(osv.osv):
    _name = "smm.fotohost"
    _description = "Фото хостинг"
    _order = 'cr_date'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_fotohost_rel', 'smm_foto_id', 'usr_id', string='Ответственный', select=True),
        'name_id':fields.many2one('smm.fotohost.stage', 'Название фото хостинга', select=True),
        'cr_date':fields.date('Дата создания', select=True),
        'account':fields.char('Аккаунт', size=255),
        'login':fields.char('Логин', size=64),
        'password':fields.char('Пароль', size=64),
        'comments':fields.text('Примечание'),
        'rights':fields.char('Права', size=255),
        'partner_id':fields.many2one('res.partner', 'Компания', select=True),
        'url':fields.char('URL', size=255),
        'email':fields.char('Эл. почта', size=255),
    }
    _defaults = {
        'cr_date':time.strftime('%Y-%m-%d'),
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
smm_fotohost()

class smm_videohost_stage(osv.osv):
    _name = "smm.videohost.stage"
    _description = "Справочник видео хостинга"
    _order = 'name'
    _columns = {
       'name': fields.char('Название видео хостинга', size=255, required=True, select=True),
    }
smm_videohost_stage()

class smm_videohost(osv.osv):
    _name = "smm.videohost"
    _description = "Видео хостинг"
    _order = 'cr_date'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_videohost_rel', 'smm_video_id', 'usr_id', string='Ответственный', select=True),
        'name_id':fields.many2one('smm.videohost.stage', 'Название видео хостинга', select=True),
        'cr_date':fields.date('Дата создания', select=True),
        'account':fields.char('Аккаунт', size=255),
        'login':fields.char('Логин', size=64),
        'password':fields.char('Пароль', size=64),
        'comments':fields.text('Примечание'),
        'types':fields.char('Тип', size=255),
        'partner_id':fields.many2one('res.partner', 'Компания', select=True),
        'url':fields.char('URL', size=255),
        'email':fields.char('Эл. почта', size=255),
    }
    _defaults = {
        'cr_date':  time.strftime('%Y-%m-%d'),
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
smm_videohost()

class smm_email_stage(osv.osv):
    _name = "smm.email.stage"
    _description = "Домены эл. почты"
    _order = 'name'
    _columns = {
       'name': fields.char('Домен эл. почты', size=255, required=True, select=True),
    }
smm_email_stage()

class smm_email(osv.osv):
    _name = "smm.email"
    _description = "Эл. почта"
    _order = 'name_id'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_email_rel', 'smm_email_id', 'usr_id', string='Ответственный', select=True),
        'name_id':fields.many2one('smm.email.stage', 'Домен эл. почты', select=True),
        'login':fields.char('Почта', size=125),
        'password':fields.char('Пароль', size=64),
        'comments':fields.text('Комментарии'),
        'pre_comment':fields.text('Примечание'),
        'recover_word':fields.char('Контрольный вопрос/ответ', size=225),
    }
    _defaults = {
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
smm_email()

class smm_blogs_stage(osv.osv):
    _name = "smm.blogs.stage"
    _description = "Название блога"
    _order = 'name'
    _columns = {
       'name': fields.char('Название', size=255, required=True, select=True),
    }
smm_blogs_stage()

class smm_blogs(osv.osv):
    _name = "smm.blogs"
    _description = "Блоги"
    _order = 'name_id'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_blogs_rel', 'smm_blog_id', 'usr_id', string='Ответственный', select=True),
        'name_id':fields.many2one('smm.blogs.stage', 'Название', select=True),
        'account':fields.char('Аккаунт', size=255),
        'login':fields.char('Логин', size=125),
        'password':fields.char('Пароль', size=64),
        'tema':fields.char('Тематика', size=255),
        'rights':fields.char('Права', size=255),
        'partner_id':fields.many2one('res.partner', 'Компания', select=True),
        'cr_date':fields.date('Дата создания', select=True),
        'url':fields.char('URL', size=255),
        'email':fields.char('Эл. почта', size=255),
        'comments':fields.text('Комментарии'),
    }
    _defaults = {
        'cr_date':time.strftime('%Y-%m-%d'),
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
smm_blogs()

class smm_stpres_stage(osv.osv):
    _name = "smm.stpres.stage"
    _description = "Название статьи/пресс-релизы"
    _order = 'name'
    _columns = {
       'name': fields.char('Название', size=255, required=True, select=True),
    }
smm_stpres_stage()

class smm_stpres_rights_stage(osv.osv):
    _name = "smm.stpres.rights.stage"
    _description = "Права статьи/пресс-релизы"
    _order = 'name'
    _columns = {
       'name': fields.char('Название прав', size=255, required=True, select=True),
    }
smm_stpres_rights_stage()

class smm_stpres_type_stage(osv.osv):
    _name = "smm.stpres.type.stage"
    _description = "Типы статьи/пресс-релизы"
    _order = 'name'
    _columns = {
       'name': fields.char('Тип', size=255, required=True, select=True),
    }
smm_stpres_type_stage()

class smm_stpres(osv.osv):
    _name = "smm.stpres"
    _description = "Статьи/Пресс-релиза"
    _order = 'name_id'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_stpres_rel', 'smm_stp_id', 'usr_id', string='Ответственный', select=True),
        'name_id':fields.many2one('smm.stpres.stage', 'Название', select=True, widget='selection'),
        'account':fields.char('Аккаунт', size=255),
        'login':fields.char('Логин', size=125),
        'password':fields.char('Пароль', size=64),
        'tema':fields.char('Тематика', size=255),
        'rights_id':fields.many2one('smm.stpres.rights.stage', 'Права', select=True, widget='selection'),
        'partner_id':fields.many2one('res.partner', 'Компания', select=True),
        'cr_date':fields.date('Дата создания', select=True),
        'url':fields.char('URL', size=255),
        'email':fields.char('Эл. почта', size=255),
        'type_id':fields.many2one('smm.stpres.type.stage', 'Тип', select=True, widget='selection'),
        'comments':fields.text('Примечание'),
    }
    _defaults = {
        'cr_date':time.strftime('%Y-%m-%d'),
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
smm_stpres()

#~ class smm_forum_stage(osv.osv):
    #~ _name = "smm.forum.stage"
    #~ _description = "Название форума"
    #~ _order = 'name'
    #~ _columns = {
       #~ 'name': fields.char('Название', size=255, required=True, select=True),
    #~ }
#~ smm_forum_stage()

class smm_forum_rights_stage(osv.osv):
    _name = "smm.forum.rights.stage"
    _description = "Права форума"
    _order = 'name'
    _columns = {
       'name': fields.char('Название прав', size=255, required=True, select=True),
    }
smm_forum_rights_stage()

class smm_forum_country_stage(osv.osv):
    _name = "smm.forum.country.stage"
    _description = "Справочник стран"
    _order = 'name'
    _columns = {
       'name': fields.char('Название страны', size=255, required=True, select=True),
    }
smm_forum_country_stage()

class smm_forum_state_stage(osv.osv):
    _name = "smm.forum.state.stage"
    _description = "Справочник регионов/областей"
    _order = 'name'
    _columns = {
       'name': fields.char('Название региона', size=255, required=True, select=True),
       'country_id':fields.many2one('smm.forum.country.stage', 'Страна', select=True),
    }
smm_forum_state_stage()

class smm_forum(osv.osv):
    _name = "smm.forum"
    _description = "Форумы"
    _order = 'name'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_forum_rel', 'smm_forum_id', 'usr_id', string='Ответственный', select=True),
        'name':fields.char('Название', size=250,select=True),
        'account':fields.char('Аккаунт', size=255),
        'login':fields.char('Логин', size=125),
        'password':fields.char('Пароль', size=64),
        'tema':fields.char('Тематика', size=255),
        'rights_id':fields.many2one('smm.forum.rights.stage', 'Права', select=True, widget='selection'),
        'partner_id':fields.many2one('res.partner', 'Компания', select=True),
        'cr_date':fields.date('Дата создания', select=True),
        'url':fields.char('URL', size=255),
        'email':fields.char('Эл. почта', size=255),
        'countrys_id':fields.many2one('smm.forum.country.stage', 'Страна', select=True),
        'states_id':fields.many2one('smm.forum.state.stage', 'Регион', select=True),
        'comments':fields.text('Примечание'),
    }
    _defaults = {
        'cr_date':time.strftime('%Y-%m-%d'),
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
smm_forum()


class smm_mobphone_func_stage(osv.osv):
    _name = "smm.mobphone.func.stage"
    _description = "Справочник функций персонажа"
    _order = 'name'
    _columns = {
       'name': fields.char('Название функции', size=255, required=True, select=True),
    }
smm_mobphone_func_stage()


class smm_mobphone(osv.osv):
    _name = "smm.mobphone"
    _description = "Мобильные телефоны"
    _order = 'date_last_check'
    _columns = {
        # Head
        'user_id': fields.many2one('res.users', 'Автор', select=True),
        'responsible_users': fields.many2many('res.users', 'res_user_smm_mobphone_rel', 'smm_mob_id', 'usr_id', string='Ответственный', select=True),
        'number': fields.integer('Номер', select=True, required=True),
        'date_activ': fields.date('Дата активации', select=True),
        'balance': fields.float('Баланс на счету'),
        'date_valid_for': fields.date ('Действителен до', select=True),
        'name_person':fields.char('Имя персонажа', size=255),
        'url':fields.char('Ссылка на персонаж', size=255),
        'function_person': fields.many2one('smm.mobphone.func.stage', 'Фукции персонажа', select=True, widget='selection'),
        'date_last_check': fields.date ('Дата последней проверки', select=True),
     }

    _defaults = {
        'user_id':  lambda self, cr, uid, context: uid,
        'responsible_users': lambda self, cr, uid, context: self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context),
    }
    def _check_number(self, cr, uid, ids):
        for field in self.browse(cr, uid, ids):
            if field.number == False or field.number == 0:
                return False
        return True
    _constraints = [
        (_check_number,
        'Необходимо ввести номер',
        ['number']),
        ]
smm_mobphone()
