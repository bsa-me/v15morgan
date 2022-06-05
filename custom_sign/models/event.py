from odoo import api, fields, models


class Event(models.Model):
    _inherit = 'event.event'

    sign_tmp_id = fields.Many2one('sign.template')
    
class EventRegistration(models.Model):
    _inherit = 'event.registration'

    sign_tmp_id = fields.Many2one(related='event_id.sign_tmp_id')

    @api.model
    def create(self, vals):
        record = super(EventRegistration, self).create(vals)
        record.env['sign.template'].browse(record.sign_tmp_id.id).write(
            {'fields_of': 'registration', 'event_reg_id': record.id})
        return record


class SignItemRole(models.Model):
    _inherit = 'sign.item'

    responsible_id = fields.Many2one("sign.item.role", string="Responsible", required=1)


class EventTicket(models.Model):
    _inherit = 'event.event.ticket'

    sign_tmp_id = fields.Many2one('sign.template','Sign Template')
