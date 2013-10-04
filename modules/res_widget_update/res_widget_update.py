# -*- coding: utf-8 -*-
from osv import fields, osv


class res_widget(osv.osv):
    _name = "res.widget"
    _inherit = "res.widget"
    _columns = {
        'html_text': fields.related(
            'content',
            type="text",
            relation="res.widget",
            string="Html"),
    }

res_widget()
