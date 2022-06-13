from odoo import api, fields, models


class Payment(models.Model):
    _inherit = 'account.payment'

    def customer_receipt_notification(self):
        template = self.env.ref('accounting_workflow.email_template_receipt_notification')
        template.email_to = self.partner_id.email
        self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)
