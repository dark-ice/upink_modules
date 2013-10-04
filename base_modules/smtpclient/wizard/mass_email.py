import wizard
import pooler
from osv import fields
from osv import osv
import time
import sys
from tools.translate import _
import tools
import re

class mass_email(osv.osv_memory):
    _name = 'mass.email'
    _columns = {
                'smtp_server' : fields.many2one('email.smtpclient','SMTP Server',required=True,domain="[('pstate','=','running'),('active','=',True)]"),
                'subject' : fields.char('Subject',size=1000,required=True),
                'body'    : fields.text('Body',required=True),
                }
    
    
    def merge_message(self, cr, uid, message, object, partner):
        def merge(match):
            exp = str(match.group()[2:-2]).strip()
            result = eval(exp, {'object':object, 'partner':partner})
            if result in (None, False):
                return str("--------")
            return str(result)
        
        com = re.compile('(\[\[.+?\]\])')
        msg = com.sub(merge, message)
        return msg
    
    # this sends an email to ALL the addresses of the selected partners.
    def mass_mail_send(self, cr, uid, ids, context):
        nbr = 0
        data = self.read(cr,uid,ids)[0]
        partners = pooler.get_pool(cr.dbname).get('res.partner').browse(cr, uid, context['active_ids'], context)
        email_server = pooler.get_pool(cr.dbname).get('email.smtpclient')
        
        for partner in partners:
            for adr in partner.address:
                if adr.email:
                    name = adr.name or partner.name
                    to = adr.email
                    subject = self.merge_message(cr, uid, data['subject'], adr, partner)
                    message = self.merge_message(cr, uid, data['body'], adr, partner)
                    email_server.send_email(cr, uid, data['smtp_server'][0], to, subject, message)
                    nbr += 1
                    
            pooler.get_pool(cr.dbname).get('res.partner.event').create(cr, uid,
                    {'name': 'Email sent through mass mailing',
                     'partner_id': partner.id,
                     'description': data['body'], })
    #TODO: log number of message sent
        return {'email_sent': nbr}
    
mass_email()