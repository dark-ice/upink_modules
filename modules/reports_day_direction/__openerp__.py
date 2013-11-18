# coding=utf-8
{
    'name': 'Ежедневные отчеты направлений',
    'version': '0.1',
    'category': 'Reports',
    'complexity': "easy",
    'description': """
Ежедневные отчеты направлений.
==============================
- PPC
    """,
    'author': 'Andrey Karbanovich',
    'website': 'http://upsale.ru',
    'depends': ['base', 'process_launch', 'process_ppc'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        #'security/ir.model.access.csv',
        'views/view_ppc.xml',
        #'workflow.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}