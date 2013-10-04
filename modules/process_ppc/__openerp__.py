# coding=utf-8
{
    'name': 'Process PPC',
    'version': '1.0',
    'category': 'Tools',
    'complexity': "easy",
    'description': """
Процесс PPC.
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
        'data.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}