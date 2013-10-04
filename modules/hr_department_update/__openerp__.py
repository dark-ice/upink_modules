# -*- coding: utf-8 -*-

{
    "name": "Human Resources Department Update",
    "version": "1.1",
    "author": "Karbanovich Andrey [Upsale dep IS]",
    "category": "Generic Modules/Human Resources",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Human Resources Update.
=====================================
Добавлены:
Рабочее время (ua, rus, eu)
Ответственный директор
    """,
    'images': [],
    'depends': ['base_setup', 'hr'],
    'init_xml': [],
    'update_xml': [
        'hr_department_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    "css": [],
}
