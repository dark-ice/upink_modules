
var __lc_buttons = [];

openerp.asterisk_incoming_calls = function (openerp) {

    openerp.asterisk_incoming_calls.Action = openerp.web.OldWidget.extend({
        template: 'Header-Asterisk-Incoming',

        start: function() {
            this._super();
            if (!this.session)
                return;
            var self = this;
            var pwc = new openerp.web.Model("asterisk.calls.config");
            return pwc.get_func('get_default_text')().then(function(text) {
                self.$element.html(text);
                self.$element.click(self.do_load_call);
            });
        },

        do_load_call: function(evt) {
            //evt.preventDefault();
            var pwc = new openerp.web.Model("activ.asterisk.calls");
            self.action_manager = new openerp.web.ActionManager(self);

            pwc.get_func('get_lead_partner_by_phone')().then(function(obj) {
                var self = this;
                var model = obj.type, type;
                var id = obj.id;
                var name = obj.name;

                if (!(model !== undefined && id !== undefined)) {
                    this.dialog = new openerp.web.Dialog(this, {
                        title: "Входящий звонок",
                        width: '300px',
                        buttons: [
                            {text: _t("Close"), click: function () {
                                $(this).dialog('destroy');
                            }},
                        ]
                    }).open();
                    this.dialog.$element.html(openerp.web.qweb.render('AsteriskIncomingView', { widget: self }));
                } else {
                    if (model == 'crm.lead') {
                        type = 'Кандидат:';
                    } else {
                        type = 'Партнер:';
                    }

                    var action = {
                        res_model: model,
                        res_id: id,
                        views: [
                            [1445, 'form']
                        ],
                        type: 'ir.actions.act_window',
                        name: type + ": " + name,
                        target: 'new',
                        nodestroy: true,
                        auto_search: true,
                        flags: {
                            sidebar: false,
                            views_switcher: true,
                            action_buttons: true
                        }
                    };
                    var action_manager = new openerp.web.ActionManager(self);
                    action_manager.do_action(action);

                }
            });

        }
    });


    openerp.web.Header.include({
        do_update: function() {
            var self = this;
            this._super();
            this.update_promise.then(function() {
                if (self.open_call) {
                    self.open_call.stop();
                }
                self.open_call = new openerp.asterisk_incoming_calls.Action(self);
                self.open_call.prependTo(self.$element.find('div.header_corner'));
            });
        }
    });
};
