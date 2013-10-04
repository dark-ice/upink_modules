# -*- encoding: utf-8 -*-

{
    "name": "Library",
    "version": "1.0",
    "author": "Karbanovich Andrey [Upsale dep IS]",
    "category": "Generic Modules",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Библиотека.
=====================================
Библиотека в ERP.
    """,
    'images': [],
    'depends': ['base', 'attachment', 'notify'],
    'init_xml': [],
    'update_xml': [
        'security/storage_files_security.xml',
        'security/ir.model.access.csv',
        'storage_files_view.xml',
        'storage_groups_view.xml',
        'storage_folders_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
}
