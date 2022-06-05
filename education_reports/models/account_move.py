from odoo import api, fields, models
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'
    country_id = fields.Many2one('res.country', related='partner_id.country_id', store=True)

    @api.depends('invoice_line_ids')
    def _update_term(self):
        if self.invoice_line_ids:
            for rec in self:
                lines = rec.invoice_line_ids.filtered(lambda l: l.term_id != False)
                if lines:
                    rec.terms = lines[0].term_id.name
