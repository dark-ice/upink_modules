//  @@@ web_export_view custom JS @@@

openerp.web_migrate = function (openerp) {
    _t = openerp.web._t;

    openerp.web.Sidebar = openerp.web.Sidebar.extend({

        add_default_sections: function () {
            var self = this,
                view = this.widget_parent,
                view_manager = view.widget_parent,
                action = view_manager.action;
            var models = ['crm.lead', 'res.partner'];
            if (this.session.uid === 1) {
                this.add_section(_t('Customize'), 'customize');
                this.add_items('customize', [{
                    label: _t("Translate"),
                    callback: view.on_sidebar_translate,
                    title: _t("Technical translation")
                }]);
            }

            if (models.indexOf(view.model) > -1) {
                this.add_section("Переприсвоение", 'migrate');
                this.add_items('migrate', [
                    {
                        label: "Переприсвоить...",
                        callback: this.on_sidebar_transfer
                    }
                ]);
            }

            this.add_section(_t('Other Options'), 'other');
            this.add_items('other', [
                {
                    label: _t("Import"),
                    callback: view.on_sidebar_import
                }, {
                    label: _t("Export"),
                    callback: view.on_sidebar_export
                }
            ]);
        },

        on_sidebar_transfer: function () {
            var self = this;
            var ids = self.widget_parent.get_selected_ids();
            var model = self.widget_parent.model;

            this.dialog = new openerp.web.Dialog(this,{
                title: "Переприсвоение на другого менеджера",
                width: '300px',
                buttons: [
                    {text: _t("Cancel"), click: function(){ self.dialog.stop(); }},
                    {text: "Переприсвоить", click: function(){
                        self.rpc(
                            "/web/transfer/managers",
                            {
                                'selected_ids': ids,
                                'model': model,
                                'manager_id': $("#managers_transfer").val()
                            },
                            function(state){
                                console.log(state);
                                self.dialog.stop();
                                window.location.reload();
                        });
                    }},
                ]
            }).open();
            this.dialog.$element.html(openerp.web.qweb.render('TransferView', { widget: self }));
            self.do_setup_managers(this.dialog.$element.find('#managers_transfer'));
        },

        do_setup_managers: function ($select) {
            var domain = [['groups_id','in',[47, 48, 49, 50, 77, 85, 74]], ['id', 'not in', [1, 5, 13, 354]]];
            var ds = new openerp.web.DataSetSearch(this, 'res.users',{}, domain);
            ds.read_slice(['name']).then(function (r) {
                _(r).each(function (record) {
                    var opt = new Option(record.name, record.id);
                    var options = $select.prop('options');
                    options[options.length] = opt;
                });
            });
        }

    });
};
