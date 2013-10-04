# coding=utf-8
{
    'name': 'Процесс Call Входящая кампания',
    'version': '1.0',
    'category': 'Tools',
    'complexity': "easy",
    'description': """
Процесс Call Входящая кампания.
==============================
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'process_launch', 'process_call'],
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