# -*- coding: utf-8 -*-

{
    "name": "CRM Update",
    "version": "1.2",
    "author": "Upsale dep IS",
    "category": "Customer Relationship Management",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Update to module CRM.
=====================================

    """,
    'images': [],
    'depends': [
        'base',
        'crm',
        'mail',
        'fetchmail',
        'brief'
    ],
    'init_xml': [],
    'update_xml': [
        'security/crm_security.xml',
        'security/ir.model.access.csv',
        'wizard/crm_lead_to_partner_view.xml',
        'wizard/note.xml',
        'crm_view.xml',
        'crm_lead_view.xml',
        'crm_lead_individual_views.xml',
        'crm_lead_eu_view.xml',
        'reports/reports_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
}
