# coding=utf-8
{
    'name': 'Финансовые отчеты',
    'version': '0.1',
    'category': 'Reports',
    'complexity': "easy",
    'application': True,
    'description': """
Финансовые отчеты.
==============================
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'account', 'process_launch'],
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