# coding=utf-8
{
    'name': 'Распоряжения',
    'version': '0.1',
    'category': 'Documents',
    'complexity': "easy",
    'description': """
Распоряжения.
==============================
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'hr', 'kpi'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        #'security/ir.model.access.csv',
        'view_items.xml',
        'view_disposition.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': ['images/process.jpg', 'images/process_hover.jpg'],
}