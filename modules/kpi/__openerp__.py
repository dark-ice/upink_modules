# -*- encoding: utf-8 -*-
{
    'name': 'KPI',
    'version': '2.0.3',
    'author': 'Karbanovich Andrey [Upsale dep IS]',
    'category': 'Generic Modules/Human Resources',
    'complexity': 'easy',
    'website': 'http://www.upsale.ru/',
    'description': """
KPI.
=====================================
Ключевые показатели эффективности (англ. Key Performance Indicators, KPI) — система оценки, которая помогает организации определить достижение стратегических и тактических (операционных) целей. Использование ключевых показателей эффективности даёт организации возможность оценить своё состояние и помочь в оценке реализации стратегии.
    """,
    'images': [],
    'depends': ['base', 'hr', 'notify'],
    'init_xml': [],
    'update_xml': [
        'security/kpi_security.xml',
        'security/ir.model.access.csv',
        'data.xml',
        'view.xml',
        'smart_view.xml',
        'kpi_view.xml',
        'report_view.xml',
        'menu.xml',
        'smart_workflow.xml',
        'kpi_workflow.xml',
    ],
    'js': [],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'css': [],
}
