# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseComment(models.TransientModel):
    _name = "event.transfer.dropout"
    registration_id = fields.Many2one('event.registration',string='registration')
    old_event_id = fields.Many2one('event.event',string='Old Event')
    new_event_id = fields.Many2one('event.event',string='New Event')
    transfer_date = fields.Date(string='Transfer Date')
    type = fields.Selection([('transfer', 'Transfer'),('dropout','Dropped Out')],string='Status',default=False)
    reason = fields.Text('Reason')

    def transfer_or_dropout_event(self):
        if self.new_event_id:
            new_registration = self.registration_id.copy()
            new_registration.write({
                'event_id': self.new_event_id.id,
                })

            body = 'This Registration was transferred from ' + self.old_event_id.name
            if self.reason:
                body = 'This Registration was transferred from ' + self.old_event_id.name + ' for the reason ' + str(self.reason)

            self.env['mail.message'].create({
                'model': 'event.registration',
                'res_id': new_registration.id,
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_note').id,
                'body': body
                })

            
            self.registration_id.write({
                'reason': self.reason,
                'transfer_status': 'transferred'
                })
            
            self.registration_id.button_reg_cancel()

            body = 'This Registration was transferred to ' + self.new_event_id.name
            if self.reason:
                body = 'This Registration was transferred to ' + self.new_event_id.name + ' for the reason ' + str(self.reason)

            self.env['mail.message'].create({
                'model': 'event.registration',
                'res_id': self.registration_id.id,
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_note').id,
                'body': body
                })

        else:
            self.registration_id.write({'reason': self.reason, 'transfer_status': 'dropout'})
            self.registration_id.button_reg_cancel()
        




