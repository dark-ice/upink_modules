# -*- encoding: utf-8 -*-

{
    "name": "Inksystem Support",
    "version": "1.6",
    "author": "Upsale dep IS",
    "category": "Sale",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Сервисный центр
=====================================

    """,
    'images': [],
    'depends': [
        'base',
        'hr',
    ],
    'init_xml': [],
    'update_xml': [
        #'security/support_inksystem_security.xml',
        #'security/ir.model.access.csv',
        'workflow.xml',
        'support_ink_view.xml',
        'support_order_report.xml',
        'report/reports_view.xml'
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
}
