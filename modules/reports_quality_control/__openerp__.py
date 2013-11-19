# coding=utf-8
{
    'name': 'Reports Quality Control',
    'version': '1.0',
    'category': 'Reports',
    'complexity': "easy",
    'description': """
Отчет по управлению качеством.
==============================
    """,
    'author': 'Dmitriy Skripnik',
    'website': 'http://upsale.ru',
    'depends': ['base', 'kpi'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'update_xml': [
        'report_quality_control_manager_view.xml',
        'report_quality_control_specialist_view.xml',
        'report_quality_control_direction_view.xml',
        'report_quality_control_partner_view.xml',
        'report_quality_control_general_view.xml',
    ],

    'js': [],
    'css': [],
    'qweb': [],
    'images': [],
}