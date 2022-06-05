odoo.define('odoo_check_all_companies.odoo_companies', function (require) {
    "use strict";
    var core = require('web.core');
    var localStorage = require('web.local_storage');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var _t = core._t;
    var ActionMenu = Widget.extend({
        template: 'check_all_companies.gift_icon',
        events: {
            'click .gift_icon': 'onclick_gifticon',
        },

        onclick_gifticon: function () {

            this.do_action('odoo_check_all_companies.action_select_companies').then(function () {
                console.log('success');
            })
        },
    });

    SystrayMenu.Items.push(ActionMenu);
    return ActionMenu;
});