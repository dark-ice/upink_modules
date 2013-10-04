# -*- coding: utf-8 -*-

import openobject.templating

class BaseTemplateEditor(openobject.templating.TemplateEditor):
    templates = ['/openobject/controllers/templates/base.mako']

    def edit(self, template, template_text):
        output = super(BaseTemplateEditor, self).edit(template, template_text)

        end_head = output.index('</head>')

        output = output[:end_head] + """
<link rel="stylesheet" type="text/css" href="/through_search/static/css/lc.css"/>
<script type="text/javascript" src="/through_search/static/js/jquery.highlight.js"></script>
        """ + output[end_head:]

        return output