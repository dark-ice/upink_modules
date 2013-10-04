# coding=utf-8
{
    'name': 'Process SMM',
    'version': '1.0',
    'category': 'Tools',
    'complexity': "easy",
    'description': """
Процесс SMM.
==============================
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'process_launch'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        'security/ir.model.access.csv',
        'view.xml',
        'workflow.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}