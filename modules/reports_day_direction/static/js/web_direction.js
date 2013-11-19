openerp.reports_day_direction = function (openerp) {
    _t = openerp.web._t;

    openerp.web.Sidebar = openerp.web.Sidebar.extend({

        init: function(parent, element_id) {
            this._super(parent, element_id);
            this.items = {};
            this.sections = {};
        },
        start: function() {
            var view = this.widget_parent,
                models = ['report.day.ppc.statistic', ];
            this._super(this);
            var self = this;
            this.$element.html(openerp.web.qweb.render('Sidebar'));
            this.$element.find(".toggle-sidebar").click(function(e) {
                self.do_toggle();
            });
            if (models.indexOf(view.model) > -1) {
                this.add_section("Обновить записи", 'update');
                this.add_items('update', [
                    {
                        label: "Обновить...",
                        callback: this.on_update
                    }
                ]);
            }
        },
        on_update: function () {
            var self = this;
            var ids = self.widget_parent.get_selected_ids();
            var model = self.widget_parent.model;

            this.dialog = new openerp.web.Dialog(this,{
                title: "Обновление информации от Яндекс.Директа",
                width: '300px',
                buttons: [
                    {text: _t("Cancel"), click: function(){ self.dialog.stop(); }},
                    {text: "Обновить", click: function(){
                        self.rpc(
                            "/web/direction/update", {'model': model},
                            function(state){
                                self.dialog.stop();
                                window.location.reload();
                        });
                    }},
                ]
            }).open();
            this.dialog.$element.html(openerp.web.qweb.render('UpdateView', { widget: self }));
        }

    });
};
