import wizard
import pooler
from osv import fields
from osv import osv
import time
import sys
from tools.translate import _

class verify_code_popup(osv.osv_memory):
    
    _name = 'verify.code'
    _columns = {
                'code':fields.char('Code', required=True, size=255),
                }
    
    def verify_code(self, cr, uid, ids, context):
        data = self.read(cr,uid,ids)[0]
        context = context or {}
        server_pool = self.pool.get('email.smtpclient')
        cron_pool = self.pool.get('ir.cron')
        server = server_pool.browse(cr, uid,context.get('active_id',0), context)
        state = server.state
        if state == 'confirm':
            raise osv.except_osv(_('Error'), _('Server already verified!'))
        code = server.code
        if code == data['code']:
            if server_pool.create_process(cr, uid, [context.get('active_id',0)], context={}):
                server_pool.write(cr, uid, [context.get('active_id',0)], {'state':'confirm', 'pstate':'running'})
                server_pool.start_process(cr, uid, [context.get('active_id',0)], context)
        else:
            raise osv.except_osv(_('Error'), _('Verification failed. Invalid Verification Code!'))
        return {'type': 'ir.actions.act_window_close'}
    
verify_code_popup()
