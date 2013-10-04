# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: Tverdochleb Sergey
#    Copyright (C) 2011 - 2012 by UpSale co
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openobject.templating


class HeaderTemplateEditor(openobject.templating.TemplateEditor):
    templates = ['/openerp/controllers/templates/header.mako']

    def edit(self, template, template_text):
        output = super(HeaderTemplateEditor, self).edit(template, template_text)

        PATTERN = '<div id="corner">'
        corner = output.index(PATTERN) + len(PATTERN)

        output = output[:corner] + u"""
                <p class="logout" id="astcalls">
                ${ rpc.session.execute('object', 'execute', 'asterisk.calls.config', 'get_button_calls') | n}
                </p>
        """ + output[corner:]
        return output

