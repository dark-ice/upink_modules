import wizard
import pooler
from osv import fields
from osv import osv
import time
import sys
from tools.translate import _

class send_code_popup(osv.osv_memory):
    
    _name = 'send.code'
    _columns = {
                'emailto':fields.char('Email Address', required=True, size=255),
                }
    
    def check_code(self, cr, uid, ids, context):
        context = context or {}
        code = self.pool.get('email.smtpclient').browse(cr, uid, context.get('active_id',0),context).code
        if code:
            raise osv.except_osv(_('Error'), _('Verification Code Already Generated !'))
        return True

    def send_code(self, cr, uid, ids, context):
        context = context or {}
        if self.check_code(cr,uid,ids,context):
            data = self.read(cr,uid,ids)[0]
            state = pooler.get_pool(cr.dbname).get('email.smtpclient').test_verify_email(cr, uid, [context.get('active_id',0)], data['emailto'])
            if not state:
                raise osv.except_osv(_('Error'), _('Verification Failed. Please check the Server Configuration!'))

        return {'type': 'ir.actions.act_window_close'}
    
send_code_popup()