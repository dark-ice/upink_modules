# -*- coding: utf-8 -*-

{
    'name': 'eInvoicing Update',
    'version': '0.33',
    'author': 'Andrey Karbanovich',
    'category': 'Accounting & Finance',
    'complexity': 'easy',
    'description': '''
Update for module Account
    ''',
    'website': 'http://upsale.ru',
    'depends': ['account', 'crm', 'notify', 'decimal_precision'],
    'update_xml': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'report_header.xml',
        'invoice_report.xml',
        'wizard/invoice_pay_view.xml',
        'wizard/invoice_document_view.xml',
        'account_view.xml',
        'account_invoice_workflow.xml',
        'report/reports_view.xml',
        'wizard/invoice_act_view.xml',
        'wizard/invoice_kassa_view.xml',
    ],
    'installable': True,
    'active': False,
}