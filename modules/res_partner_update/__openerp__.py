# -*- coding: utf-8 -*-

{
    'name': 'CRM - Partner Update',
    'version': '1.12',
    'category': 'Customer Relationship Management',
    'author': 'Andrey Karbanovich [UpSale&Inksystem]',
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Res.Partner Update
=====================================
""",
    'depends': [
        'base',
        'crm',
        'brief',
        'crm_lead_update',
    ],
    'update_xml': [
        'security/partner_security.xml',
        'security/ir.model.access.csv',
        'wizard/quality_view.xml',
        'wizard/service_view.xml',
        'wizard/service_report_view.xml',
        'partner_view.xml',
        'partner_individual_views.xml',
        'partner_eu_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
