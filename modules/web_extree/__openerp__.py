# coding=utf-8
{
    "name": "Extra Tree",
    "category": "Hidden",
    "description":
    """
    OpenERP Web extra view.
    """,
    "version": "2.0",
    "depends": ["web"],
    "js": [
        "static/src/js/extree.js"
    ],
    "css": [
        "static/src/css/extree.css"
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'auto_install': True
}
