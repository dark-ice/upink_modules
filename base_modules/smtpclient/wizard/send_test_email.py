import wizard
import pooler
from osv import fields
from osv import osv
import time
import sys
from tools.translate import _

class send_test_email(osv.osv_memory):
    _name = 'send.test.email'
    _columns = {
                'emailto':fields.char('Email Address', required=True, size=255),
                }
    
    def send_test_email(self, cr, uid, ids, context):
        data = self.read(cr,uid,ids)[0]
        state = pooler.get_pool(cr.dbname).get('email.smtpclient').test_verify_email(cr, uid, context.get('active_ids'), data['emailto'], test=True)
        if not state:
            raise osv.except_osv(_('Error'), _('Verification Failed. Please check the Server Configuration!'))
        return {}

send_test_email()