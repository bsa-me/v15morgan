from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def customer_quotation_notification(self):
        template = self.env.ref('accounting_workflow.email_template_quotation_notification')
        template.email_to = self.partner_id.email
        self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)
