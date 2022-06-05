odoo.define('education.product_event_configurator', function (require) {
var ProductConfiguratorWidget = require('event_sale.product_configurator');


ProductConfiguratorWidget.include({

    _onEditLineConfiguration: function () {
        if (this.recordData.event_ok) {
            var defaultValues = {
                default_product_id: this.recordData.product_id.data.id,
                default_company_id: this.recordData.company_id.data.id
            };

            if (this.recordData.event_id) {
                defaultValues.default_event_id = this.recordData.event_id.data.id;
            }

            if (this.recordData.event_ticket_id) {
                defaultValues.default_event_ticket_id = this.recordData.event_ticket_id.data.id;
            }

            this._openEventConfigurator(defaultValues, this.dataPointID);
        } else {
            this._super.apply(this, arguments);
        }
    },


    _openEventConfigurator: function (data, dataPointId) {
        var self = this;
        data['default_company_id'] = this.recordData.company_id.data.id;
        console.log(data);
        this.do_action('event_sale.event_configurator_action', {
            additional_context: data,
            on_close: function (result) {
                if (result && !result.special) {
                    self.trigger_up('field_changed', {
                        dataPointID: dataPointId,
                        changes: result.eventConfiguration,
                        onSuccess: function () {
                            // Call post-init function.
                            self._onLineConfigured();
                        }
                    });
                } else {
                    if (!self.recordData.event_id || !self.recordData.event_ticket_id) {
                        self.trigger_up('field_changed', {
                            dataPointID: dataPointId,
                            changes: {
                                product_id: false,
                                name: ''
                            },
                        });
                    }
                }
            }
        });
    },
});


return ProductConfiguratorWidget;

});
