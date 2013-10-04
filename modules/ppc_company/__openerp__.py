# -*- encoding: utf-8 -*-

{
    "name": "PPC - Company",
    "version": "1.0",
    "author": "Karbanovich Andrey [Upsale dep IS]",
    "category": "Processes",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
PPC - Company.
=====================================
Start & implementation PPC company
    """,
    'images': [],
    'depends': [
        'base',
        'crm',
        'res_partner_update',
        'process_base',
        'document',
        'notify'
    ],
    'init_xml': [],
    'update_xml': [
        'ppc_company_view.xml',
        'ppc_company_workflow.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
    }
