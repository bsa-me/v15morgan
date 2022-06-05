odoo.define('education.event_ticket', function (require) {
'use strict';

console.log('Event ticket running');

var publicWidget = require('web.public.widget');

publicWidget.registry.websiteEventTicket = publicWidget.Widget.extend({
    selector: '.js_cart_lines',
    events: {
        'change .event_ticket_id': '_onEventTicketSelect',
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onEventTicketSelect: function (ev) {
        ev.preventDefault();

        var data = $(".event_ticket_id").val();
        var result = data.split("-");
        var line_id = parseInt(result[0]);
        var event_id = parseInt(result[1]);
        var event_ticket_id = parseInt(result[2]);
        var price_unit = parseFloat(result[3]);
        var vals = {"line_id": line_id, "event_id": event_id, "event_ticket_id": event_ticket_id, "price_unit": price_unit};

        this._rpc({
            route: '/update_line',
            params: vals,
        }).then(function (res) {

            setTimeout(function(){
                window.location.reload(1);
            }, 2000);
        });

    },
});

});
