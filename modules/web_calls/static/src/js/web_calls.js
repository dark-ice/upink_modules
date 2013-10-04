
openerp.web_calls = function(instance) {

instance.web_calls.CallReport = instance.web.OldWidget.extend({
    template: 'Header-CallReport',

    init: function() {
        this._super.apply(this, arguments);

    },

    start: function() {
        this._super();

        var self = this;
        var pwc = new instance.web.Model("web.calls");

        return pwc.get_func('get_default_text')().then(function(text) {
            self.$element.html(text);
            self.$element.click(function(e) {
                e.preventDefault();

                pwc.get_func('open_call')().then(function(obj) {
                    var self = this;
                    var phone = obj.phone;
                    var city = obj.city;
                    var region = obj.region;
                    var date = obj.date;
                    var time = obj.time;
                    var responsible_id = obj.responsible_id;
                    var responsible = obj.responsible;
                    self.dialog = new instance.web.Dialog(this, {
                    title: "Входящий звонок",
                    width: '700px',
                    buttons: [
                        {text: _t("Cancel"), click: function(){ $(this).dialog('destroy'); }},
                        {text: "Ок", click: function(){
                            instance.webclient.rpc("/web/calls/create",{
                                'account': $("#account").val(),
                                'call_date': date,
                                'call_time': time,
                                'call_type': $("input[name='call_type']:checked").val(),
                                'city': city,
                                'region': region,
                                'consultation': $("#consultation-val").val(),
                                'invoice': $("#invoice").val(),
                                'no_product': $("#no_product-val").val(),
                                'sale_type': $("#sale_type").val(),
                                'phone': phone,
                                'po': $("#po").val(),
                                'responsible_id': responsible_id
                            }, function(){
                                $(this).dialog('destroy');
                                window.location.reload();
                            });
                        }},
                    ]
                }).open();
                self.dialog.$element.html(instance.web.qweb.render('CallReportView', { widget: self }));

                self.dialog.$element.find('.dop').hide();
                self.dialog.$element.find('.call_type').live('click', function(){
                    var s = $(this), call_type = s.val();
                    self.dialog.$element.find('.dop').hide();
                    self.dialog.$element.find('#' + call_type).show();
                });

                self.dialog.$element.find('#region').val(region);
                self.dialog.$element.find('#city').val(city);
                self.dialog.$element.find('#phone').val(phone);
                self.dialog.$element.find('#date').val(date);
                self.dialog.$element.find('#time').val(time);
                self.dialog.$element.find('#responsible').val(responsible);
                self.dialog.$element.find('#responsible_id').val(responsible_id);

                });
                return false;
            });
        });
        

    },

});


instance.web.Header.include({
    do_update: function() {
        var self = this;
        this._super();
        this.update_promise.then(function() {
            if (self.calls) {
                self.calls.stop();
            }
            self.calls = new instance.web_calls.CallReport(self);
            self.calls.prependTo(self.$element.find('div.header_corner'));
            self.calls.rpc = self.rpc
        });
    }
});


};

