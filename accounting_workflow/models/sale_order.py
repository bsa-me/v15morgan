from odoo import api, fields, models
import base64


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    reminder_days = fields.Integer('Reminder Days',
                                   help='Send notification to the customer before (reminder_days) of'
                                        'expiration date of quotation,'
                                        'e.g: if the expiration date 25/12/2022 and reminder_days=3,'
                                        ' the customer will get notified at 22/12/2022 '
                                        'that his quote will expire in 3 days')

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

    def customer_payment_acceptance_notification(self):
        data_ids = []
        email_template = self.env.ref('accounting_workflow.email_template_payment_acceptance_notification')
        email_template.email_to = self.partner_id.email

        invoice = self.invoice_ids[0]
        payment = self.env['account.payment'].search([('ref', '=', invoice.payment_reference)], limit=1)

        # related invoice report
        data_invoice_id = self.generate_invoice_pdf(invoice)
        if data_invoice_id:
            data_ids.append(data_invoice_id)
        # payment report of invoice related to SO
        data_payment_id = self.generate_payment_pdf(payment)
        if data_payment_id:
            data_ids.append(data_payment_id)

        email_template.attachment_ids = [(6, 0, data_ids)]
        self.env['mail.template'].sudo().browse(email_template.id).send_mail(self.id)

    def generate_invoice_pdf(self, invoice):
        report_id = self.env.ref('account.account_invoices')._render_qweb_pdf(invoice.id)
        data_record = base64.b64encode(report_id[0])
        ir_values = {
            'name': "Customer Invoice",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        return data_id.id if data_id else False

    def generate_payment_pdf(self, payment):
        report_id = self.env.ref('account.action_report_payment_receipt')._render_qweb_pdf(payment.id)
        data_record = base64.b64encode(report_id[0])
        ir_values = {
            'name': "Customer Payment",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        return data_id.id if data_id else False
