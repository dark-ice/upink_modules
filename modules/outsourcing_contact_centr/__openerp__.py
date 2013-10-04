# -*- encoding: utf-8 -*-
{
    'name': 'Outsourcing Contact Center',
    'version': '1.6',
    'category': 'Sale',
    'description': """
    """,
    'author': 'Karbanovich Andrey [UpSale&InkSystem dep IS]',
    'website': 'http://www.upsale.ru',
    'depends': ['base', 'crm', 'res_partner_update', 'process_base', 'notify'],
    'update_xml': [
        'security/contact_center_security.xml',
        'security/ir.model.access.csv',
        'contact_center_stages_view.xml',
        'views/income.xml',
        'views/out.xml',
        'process/income.xml',
        'process/out.xml',
    ],
    'installable': True,
    'active': False,
}
