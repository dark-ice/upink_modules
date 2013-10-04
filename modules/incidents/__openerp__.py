# -*- encoding: utf-8 -*-
{
    'name': 'Реестр инцидентов INK',
    'version': '1.0',
    'author': 'Karbanovich Andrey [Upsale dep IS]',
    'category': '',
    'complexity': 'easy',
    'website': 'http://www.upsale.ru/',
    'description': """
Реестр инцидентов INK.
=====================================
    """,
    'images': [],
    'depends': ['base', 'notify', 'hr'],
    'init_xml': [],
    'update_xml': [
        'security/incidents_security.xml',
        'security/ir.model.access.csv',
        'view.xml',
        'workflow.xml',
    ],
    'js': [],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'css': [],
}
