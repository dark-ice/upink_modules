# coding=utf-8
{
    'name': 'Распоряжения',
    'version': '1.0',
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
        'security/disposition_security.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_view.xml',
        'view_items.xml',
        'view_disposition.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}