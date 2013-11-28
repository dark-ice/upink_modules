# -*- coding: utf-8 -*-
try:
    import json
except ImportError:
    import simplejson as json

import web.common.http as openerpweb


class Update(openerpweb.Controller):
    _cp_path = '/web/direction'

    def fields_get(self, req, model):
        Model = req.session.model(model)
        fields = Model.fields_get(False, req.session.eval_context(req.context))
        return fields

    @openerpweb.jsonrequest
    def update(self, req, model):
        cards = req.session.model(model).update()
        return [{'state': cards}]