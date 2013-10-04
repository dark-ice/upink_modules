{
    "name" : "Email Client",
    "version" : "6.1",
    "depends" : ["base"],
    "author" : "Tiny/Axelor",
    "description": """Email Client module that provides:
    Sending Email
    Use Multiple Server
    Multi Threading
    Multi Attachment
    
    *****************************************************************
    SMTPclient V6.1 modification done by : Emipro Technologies
    
    Visit : www.emiprotechnologies.com
    
    For Feedback please contact on : info@emiprotechnologies.com
    *****************************************************************
    
    
    """,
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules",
    "init_xml" : [],
    "demo_xml" : [
        "smtpclient_demo.xml"
    ],
    "update_xml" : [
        "smtpclient_view.xml",
        "serveraction_view.xml",
        "security/ir.model.access.csv",
        "smtpclient_data.xml",
        "wizard/send_code_view.xml",
        "wizard/verify_code_view.xml",
        "wizard/send_test_email_view.xml",
        "wizard/mass_mail_view.xml",
    ],
    "active": False,
    'application': True,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

