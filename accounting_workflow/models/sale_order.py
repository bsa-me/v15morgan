from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    reminder_days = fields.Integer('Reminder Days')

    def customer_quotation_notification(self):
        template = self.env.ref('accounting_workflow.email_template_quotation_notification')
        template.email_to = self.partner_id.email
        self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)

    def _cron_check_quotation_expiry_days(self):
        quotations = self.env['sale.order'].search([('state', '=', 'draft'), ('reminder_days', '>', 0)])
        for rec in quotations:
            if rec.validity_date.day - fields.Date.today().day == rec.reminder_days:
                template = rec.env.ref('accounting_workflow.reminder_expired_date_quotation_notification')
                template.email_to = rec.partner_id.email
                rec.env['mail.template'].sudo().browse(template.id).send_mail(rec.id)
