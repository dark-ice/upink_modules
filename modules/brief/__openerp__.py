# -*- encoding: utf-8 -*-

{
    "name": "CRM - Brief",
    "version": "1.3",
    "author": "Upsale dep IS",
    "category": "Customer Relationship Management",
    'complexity': "easy",
    "website": "http://www.upsale.ru/",
    "description": """
Модуль Брифы на просчет.
=====================================

UPDATE brief_main SET sum_mediaplan=cast(sum_mediaplan_moved0 as double precision);
UPDATE brief_main SET "from"= NULL;

['|', '|', '|', '&', ('responsible_user', '=', uid), ('state', 'in', ('draft', 'cancel', 'rework', 'media_approval', 'partner_refusion', 'media_approved')), '&', ('specialist_id', '=', uid), ('state', 'in', ('accept', 'inwork', 'media_accept_rev', 'media_approval_r')), ('brief_super.users.id', '=', uid), ('services_ids.leader_group_id.users.id', '=', uid)]
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
        'security/brief_security.xml',
        'security/ir.model.access.csv',
        'brief_view.xml',
        'brief_reference_view.xml',
        'brief_menu.xml',
        'brief_workflow.xml',
        'brief_data.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "css": [],
}
