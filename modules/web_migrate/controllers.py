# -*- coding: utf-8 -*-
from __future__ import print_function

try:
    import json
except ImportError:
    import simplejson as json

import web.common.http as openerpweb


class Transfer(openerpweb.Controller):
    _cp_path = '/web/transfer'

    def fields_get(self, req, model):
        Model = req.session.model(model)
        fields = Model.fields_get(False, req.session.eval_context(req.context))
        return fields

    @openerpweb.jsonrequest
    def managers(self, req, selected_ids, model, manager_id):
        m_uid = req.session._uid
        req.session._uid = 1
        user = req.session.model('res.users').read(int(manager_id), ['context_section_id'])
        cards = req.session.model(model).write(
            selected_ids,
            {
                'user_id': manager_id,
                'section_id': user['context_section_id'][0],
                'transfer_ids': [(0, 0, {'name': manager_id, 'user_id': m_uid})]
            })
        brief_ids = req.session.model('brief.main').search([('partner_id', 'in', selected_ids)])
        if brief_ids:
            briefs = req.session.model('brief.main').write(brief_ids, {'responsible_user': manager_id})

        brief_contract_ids = req.session.model('brief.contract').search([('partner_id', 'in', selected_ids)])
        if brief_contract_ids:
            briefs_contract = req.session.model('brief.contract').write(brief_contract_ids, {'usr_id': manager_id})

        brief_meeting_ids = req.session.model('brief.meeting').search([('partner_id', 'in', selected_ids)])
        if brief_meeting_ids:
            brief_meeting = req.session.model('brief.meeting').write(brief_meeting_ids, {'usr_id': manager_id})

        launch_ids = req.session.model('process.launch').search([('partner_id', 'in', selected_ids)])
        if launch_ids:
            launch = req.session.model('process.launch').write(launch_ids, {'responsible_id': manager_id})
        return [{'state': cards}]