from odoo import api, fields, models, _
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_reminder_days_before = fields.Integer('Payment Reminder Days Before', default=5, required=1)
    payment_reminder_days_after = fields.Integer('Payment Reminder Days After', default=5, required=1)

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

    def customer_payment_acceptance_notification(self):
        data_ids = []
        email_template = self.env.ref('accounting_workflow.email_template_payment_acceptance_notification')
        email_template.email_to = self.partner_id.email

        payment = self.env['account.payment'].search([('ref', '=', self.payment_reference)], limit=1)

        # related invoice report
        data_invoice_id = self.generate_invoice_pdf()
        if data_invoice_id:
            data_ids.append(data_invoice_id)

        # payment report of invoice related to SO
        data_payment_id = self.generate_payment_pdf(payment)
        if data_payment_id:
            data_ids.append(data_payment_id)

        email_template.attachment_ids = [(6, 0, data_ids)]
        self.env['mail.template'].sudo().browse(email_template.id).send_mail(self.id)

    def generate_invoice_pdf(self):
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

    def _cron_future_payment_reminder(self):
        invoices = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', '!=', 'paid'),
             ('amount_residual', '!=', 0)])
        for rec in invoices:
            for line in rec.line_ids:
                reminder_days = line.date_maturity.days - fields.Date.today().day
                if reminder_days == rec.payment_reminder_days_before and not line.reconciled:
                    self.send_payment_reminder_to_customer(rec, line.date_maturity,
                                                           line.amount_currency)

    def send_payment_reminder_to_customer(self, invoice, due_date, amount):
        email_template = self.env.ref('accounting_workflow.email_template_invoice_notification')
        email_template.email_to = invoice.partner_id.email
        email_context = {
            'due_date': due_date,
            'amount': amount,
            'invoice_number': invoice.name,
            'partner_name': invoice.partner_id.name,
        }
        self.env['mail.template'].sudo().browse(email_template.id).with_context(email_context).send_mail(self.id)
