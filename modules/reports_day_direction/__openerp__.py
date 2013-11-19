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
    'depends': ['base', 'web', 'process_launch', 'process_ppc', 'process_seo'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        #'security/ir.model.access.csv',
        'views/view_ppc.xml',
        #'workflow.xml',
    ],

    'js': [
        'static/js/web_direction.js',
    ],
    'qweb': [
        "static/xml/base.xml",
    ],
    'images': [],
}