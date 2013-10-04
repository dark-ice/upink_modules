# -*- encoding: utf-8 -*-
{
    'name': 'SMM - Start and Implementation',
    'version': '1.0',
    'category': 'SMM tools',
    'description': """
    """,
    'author': 'Upsale dep IS',
    'website': 'http://www.upsale.ru',
    'depends': [
        'base',
        'crm',
        'brief',
        'res_partner_update',
        'process_base',
        'notify'
    ],
    'update_xml': [
        'smm_strategy_view.xml',
        'smm_strategy_workflow.xml',
        #'deadlines_data.xml',
    ],
    'installable': True,
    'active': False,
}

