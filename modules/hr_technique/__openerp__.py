# coding=utf-8
{
    'name': 'Учет техники',
    'version': '0.1',
    'category': 'Tools',
    'complexity': "easy",
    'description': """
Учет техники.
==============================
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'hr', 'account'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        'security/hr_technique.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_view.xml',
        'view.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}