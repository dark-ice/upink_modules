# -*- encoding: utf-8 -*-

{
    "name": "Tasks",
    "version": "1.2.8",
    "author": "Karbanovich Andrey [Upsale dep IS]",
    "category": "Generic Modules",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Module for Tasks.
=====================================
Ставим задачи и выполняем их :)
    """,
    'images': ['images/tasks_a.png', 'images/tasks_b.png'],
    'depends': ['base', 'notify'],
    'init_xml': [],
    'update_xml': [
        'security/tasks_security.xml',
        'security/ir.model.access.csv',
        'workflow.xml',
        'view.xml',
        #'tasks_data.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
}


