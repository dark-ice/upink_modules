console.log('asas');

openerp.kpi = function (openerp) {

    openerp.kpi.Action = openerp.web.OldWidget.extend({
        template: 'Header-kpi',

        init: function() {
            console.log('sasa');
            /*
            return pwc.get_func('get_default_text')().then(function(text) {
                self.$element.html(text);
                self.$element.click(self.do_load_call);
            }); */
        }
    })
}