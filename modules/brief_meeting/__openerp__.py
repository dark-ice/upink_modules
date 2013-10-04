# -*- encoding: utf-8 -*-

{
    "name": "CRM - Brief Meeting",
    "version": "1.0",
    "author": "Upsale dep IS",
    "category": "Customer Relationship Management",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Брифы на встречу.
=====================================

    """,
    'images': [],
    'depends': [
        'base',
        'crm',
        'document',
        'notify'
    ],
    'init_xml': [],
    'update_xml': [
        'security/meeting_security.xml',
        'security/ir.model.access.csv',
        'workflow.xml',
        'view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
}
