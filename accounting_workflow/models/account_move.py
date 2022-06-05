from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def customer_invoice_notification(self):
        template = self.env.ref('accounting_workflow.email_template_invoice_notification')
        template.email_to = self.partner_id.email
        self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)
