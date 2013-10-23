# coding=utf-8
{
    'name': 'Финансовые отчеты',
    'version': '0.2',
    'category': 'Reports',
    'complexity': "easy",
    'application': True,
    'description': """
Финансовые отчеты.
==============================
- PPC
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': [
        'base',
        'account',
        'process_launch',
        'kpi',
        'res_partner_update'
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        'workflows/ppc.xml',
        'workflows/seo.xml',
        'workflows/smm.xml',
        'workflows/call.xml',
        'workflows/site.xml',
        'workflows/video.xml',
        'views/view_account_invoice_pay_line.xml',
        'views/ppc.xml',
        'views/seo.xml',
        'views/smm.xml',
        'views/call.xml',
        'views/site.xml',
        'views/video.xml',
    ],
    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}