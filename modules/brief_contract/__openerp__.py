# -*- encoding: utf-8 -*-
{
    'name': 'Brief Contract',
    'version': '1.1',
    'category': 'Customer Relationship Management',
    'description': """
    Брив на Договор
    """,
    'author': 'Karbanovich Andrey [Upsale dep IS]',
    'website': 'http://www.upsale.ru',
    'depends': [
        'base',
        'brief',
        'res_partner_update',
        'attachment_files',
        'notify'
    ],
    'update_xml': [
        'security/contract_security.xml',
        'security/ir.model.access.csv',
        'workflow.xml',
        'view.xml',
    ],
    'installable': True,
    'active': False,
}
