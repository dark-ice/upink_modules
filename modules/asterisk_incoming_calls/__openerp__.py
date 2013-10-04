# -*- coding: utf-8 -*-

{
    'name': 'Asterisk Incoming Calls',
    'version': '2.0',
    'category': 'Tools',
    'complexity': "easy",
    'description': """
Module Asterisk Incoming Calls.
=====================================
On incoming call, will open lead-partner
    """,
    'author': 'Upsale dep IS',
    'website': 'http://www.upsale.ru/',
    'depends': ['base', 'asterisk'],
    'update_xml': [],
    'js': [
        'static/js/asterisk_incoming_calls.js',
    ],
    'css': [
        'static/css/uservoice.css',
    ],
    'qweb': [
        "static/xml/*.xml",
    ],
    'installable': True,
    'auto_install': False,
    'images': ['static/images/ast_call_butt_beta.png'],
}

