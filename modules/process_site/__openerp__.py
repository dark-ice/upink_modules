# coding=utf-8
{
    'name': 'Process Site',
    'version': '0.1',
    'category': 'Tools',
    'complexity': "easy",
    'description': """
Процесс Site.

==============================
    """,
    'author': 'Karbanovich Andrey',
    'website': 'http://upsale.ru',
    'depends': ['base', 'process_launch'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        'workflows/site_workflow.xml',
        'workflows/planning_workflow.xml',
        'workflows/design_workflow.xml',
        'workflows/makeup_workflow.xml',
        'workflows/developing_workflow.xml',
        'workflows/testing_workflow.xml',
        'views/view.xml',
        'views/site_view.xml',
        'views/planning_view.xml',
        'views/design_view.xml',
        'views/testing_view.xml',
        'views/makeup_view.xml',
        'views/developing_view.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}