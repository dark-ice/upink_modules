# coding=utf-8
{
    'name': 'Финансовые отчеты',
    'version': '1.0',
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
        'views/view_account_invoice_pay_line.xml',
        'views/ppc.xml',
    ],
    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}