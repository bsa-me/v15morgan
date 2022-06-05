odoo.define('website_event_sale.payment', function(require) {
    "use strict";

    var ajax = require('web.ajax');

    $(document).ready(function() {
        'use strict';
        $("button#o_payment_form_pay").bind("click", function(ev) {
            
            var exam_id = $('select[name="exam_id"]').val();
            ajax.jsonRpc('/shop/exam_window/', 'call', {
                'exam_id': exam_id
            })
        });
    });
});