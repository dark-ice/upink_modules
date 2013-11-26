# -*- encoding: utf-8 -*-
{
    'name': 'Brief Contract',
    'version': '1.5',
    'category': 'Customer Relationship Management',
    'description': """
    Брив на Договор:
    - Генерация договора из шаблона
    - Отправка договора на сервер
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
