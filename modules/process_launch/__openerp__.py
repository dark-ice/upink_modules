# coding=utf-8
{
    'name': 'Process launch',
    'version': '1.0',
    'category': 'Tools',
    'complexity': "easy",
    'description': """
Единая карточка запуска процессов.
==============================
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'brief', 'brief_contract', 'account_update', 'kpi'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        'security/ir.model.access.csv',
        'views/view.xml',
        'views/item_view.xml',
        'wizard/sla_view.xml',
        'workflow.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': ['images/process.jpg', 'images/process_hover.jpg'],
}