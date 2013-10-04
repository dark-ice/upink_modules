# -*- coding: utf-8 -*-

{
    "name": "Human Resources Update",
    "version": "1.5",
    "author": "Karbanovich Andrey [Upsale dep IS]",
    "category": "Generic Modules/Human Resources",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Human Resources Update.
=====================================
Добавлены:
Рабочий skype
Является руководителем
    """,
    'images': [],
    'depends': ['base_setup', 'hr', 'kpi'],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'wizard/view.xml',
        'views/hr_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'css': ['static/src/css/hr.css'],
}
