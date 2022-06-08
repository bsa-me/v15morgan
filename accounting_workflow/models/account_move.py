from odoo import api, fields, models, _
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    def customer_invoice_notification(self):
        template = self.env.ref('accounting_workflow.email_template_invoice_notification')
        template.email_to = self.partner_id.email
        self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)

    def customer_refund_notification(self):
        template = self.env.ref('accounting_workflow.email_template_refund_notification')
        template.email_to = self.partner_id.email
        self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)

    def customer_credit_note_notification(self):
        template = self.env.ref('accounting_workflow.email_template_credit_note_finalizing_notification')
        template.email_to = self.partner_id.email
        self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)

    def customer_account_creation_notification(self):
        email_template = self.env.ref('accounting_workflow.email_template_account_creation_notification')
        email_template.email_to = self.partner_id.email

        report_id = self.env.ref('account.account_invoices')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_id[0])
        ir_values = {
            'name': "Customer Invoice",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)

        email_template.attachment_ids = [(6, 0, [data_id.id])]
        self.env['mail.template'].sudo().browse(email_template.id).send_mail(self.id)
