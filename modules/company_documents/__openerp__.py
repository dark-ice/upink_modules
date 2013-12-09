# -*- coding: utf-8 -*-
{
    'name': 'Company Documents',
    'version': '1.9.5',
    'category': "Generic Modules",
    'complexity': "easy",
    'description': """
    Служебные документы:
        HelpDesk
        Распоряжения
    """,
    'author': 'Karbanovich Andrey [Upsale dep IS]',
    'website': 'http://www.upsale.ru/',
    'depends': [
        'base',
        'hr',
        'hr_update',
        'notify'
    ],
    'images': [],
    'update_xml': [
        #'security/ir.model.access.csv',
        'views/helpdesk.xml',
        'company_documents.xml',
        'company_documents_data.xml',
        'company_documents_workflow.xml',
        'company_documents_disposal_workflow.xml',
        'company_documents_problem_note_workflow.xml',
        #'company_documents_helpdesk_workflow.xml',
        'process/helpdesk.xml',
        'process/disposal.xml',
        'company_documents_production_note_workflow.xml',

    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'css': [],
}
