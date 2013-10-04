# coding=utf-8

{
    'name': 'Ежедневные отчеты',
    'version': '0.9',
    'category': 'Reports',
    'complexity': "easy",
    'application': True,
    'description': """
Ежедневные отчеты.
==============================
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'account'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        'views/view_plan.xml',
        'views/view_planning.xml',
        'views/view_source.xml',
        'views/view_structure.xml',
        'views/view_mp.xml',
        'wizard.xml',
        'everyday_report.xml',
    ],
    'js': [],
    'css': ['static/style.css'],
    'qweb': [],
    'images': [],
}