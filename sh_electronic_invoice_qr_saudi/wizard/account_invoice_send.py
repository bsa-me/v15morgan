from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceSend, self).default_get(fields)
        invoices = self.env['account.move'].sudo().browse(res['invoice_ids'])
        if invoices.mapped('company_id').ids in [141, 1156, 1157, 1158]:
            res.update({
                'template_id': 71,
            })
        return res
