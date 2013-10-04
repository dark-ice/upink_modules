# -*- encoding: utf-8 -*-

{
    "name": "Notify",
    "version": "1.2",
    "author": "Karbanovich Andrey [Upsale dep IS]",
    "category": "Other",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Module for Notify.
=====================================
Уведомления:
- перевод с одного этапа на другой
- уведомление о изменении карточки и тп
- просто сообщения

Приходят:
- почта
- skype [в планах]
    """,
    'images': [],
    'depends': ['base', 'mail'],
    'init_xml': [],
    'update_xml': [
        'view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
    }
