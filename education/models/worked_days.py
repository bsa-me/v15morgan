from odoo import models, fields,api
from odoo.exceptions import UserError
from datetime import datetime


class PayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    date = fields.Date('Date')
    name = fields.Char(string='Description',store=True,readonly=False,related=False)
    contract_id = fields.Many2one('hr.contract','Contract',store=True,related=False,required=False)
    work_entry_type_id = fields.Many2one(required=False)
    display_type = fields.Selection([('line_section', "Section"),('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    contract_currency_id = fields.Many2one('res.currency',related="contract_id.company_id.currency_id")
    session_id = fields.Many2one('event.track','Session')
    amount = fields.Monetary(currency_field='contract_currency_id')
    currency_usd = fields.Many2one('res.currency',compute="_compute_usd")
    amount_usd = fields.Monetary(currency_field='currency_usd',string='Amount($)',compute="_compute_usd")
    term_id = fields.Many2one(related='session_id.event_id.term_id',store=True,string='Term')

    def _compute_usd(self):
        for record in self:
            date = datetime.now().strftime('%Y-%m-%d')
            record['currency_usd'] = self.env.ref('base.USD').id
            if record.payslip_id.company_id:
                record['amount_usd'] = record.contract_currency_id._convert(record.amount,self.env.ref('base.USD'),record.payslip_id.company_id,date)

            else:
                record['amount_usd'] = 0
