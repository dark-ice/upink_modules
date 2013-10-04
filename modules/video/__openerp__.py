# -*- encoding: utf-8 -*-
{
    'name': 'Video',
    'version': '0.2',
    'category': 'Processes',
    'description': """
    БП Video
    """,
    'author': 'Karbanovich Andrey [Upsale dep IS]',
    'website': 'http://www.upsale.ru',
    'depends': ['base', 'process_base', 'res_partner_update', 'notify'],
    'update_xml': [
        'security/video_security.xml',
        'security/ir.model.access.csv',
        'workflow.xml',
        'views/start.xml',
    ],
    'installable': True,
    'active': False,
}
