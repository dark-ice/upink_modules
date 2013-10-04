# -*- coding: utf-8 -*-
from osv import osv
from notify import notify


class CompanyDocument(object):
    _name = ""
    _workflow = ""
    _log_create = True

    _columns = {}

    states = ()

    def create(self, cr, user, vals, context=None):
        #self.log(cr, user, id, "Документ: %s под номером №%s продублировано." % id)
        return super(osv.osv, self).create(cr, user, vals, context)

    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        #self.log(cr, uid, id, "Задание №%s продублировано." % id)
        return super(osv.osv, self).read(cr, user, ids, fields, context, load)

    def browse(self, cr, user, select, context=None, list_class=None, fields_process=None):
        #self.log(cr, uid, id, "Задание №%s продублировано." % id)
        return super(osv.osv, self).browse(cr, user, select, context, list_class, fields_process)

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #self.log(cr, uid, id, "Задание №%s продублировано." % id)
        return super(osv.osv, self).search(cr, user, args, offset, limit, order, context, count)

    @notify.msg_send(_name, _workflow)
    def write(self, cr, user, ids, values, context=None):
        #self.log(cr, uid, id, "Задание №%s продублировано." % id)
        return super(osv.osv, self).write(cr, user, ids, values, context)

    def copy(self, cr, user, id, default=None, context=None):
        #self.log(cr, uid, id, "Задание №%s продублировано." % id)
        return super(osv.osv, self).copy(cr, user, id, default, context)

    def unlink(self, cr, user, ids, context=None):
        #self.log(cr, uid, id, "Задание №%s продублировано." % id)
        return super(osv.osv, self).unlink(cr, user, ids, context)

    def workflow_setter(self, cr, user, ids, state='draft'):
        return self.write(cr, user, ids, {'state': state})

    def get_state(self, state):
        return [item for item in self.states if item[0] == state][0]