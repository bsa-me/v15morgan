from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class UtmCampaign(models.Model):
    _inherit = "utm.campaign"
    expense_ids = fields.One2many('hr.expense','campaign_id',string='Expenses')
    company_id = fields.Many2one(string="Region", domain="[('is_region', '=', True)]",default=lambda self: self._get_child_companies())
    cost_per_lead = fields.Float(compute="_compute_cost_per_lead",string='Cost Per Lead')
    currency_usd = fields.Many2one('res.currency',compute="compute_currency_usd")
    expense_count = fields.Integer(compute="compute_nb_expenses")
    cost_per_acquisition = fields.Float(compute="_compute_cost_per_acquisition",string='Cost Per Acquisition')
    roi = fields.Float(compute="_compute_roi",string='ROI')
    mrm_purpose = fields.Char('MRM Purpose')
    mrm_term_id = fields.Many2one('term','MRM TERM')
    mrm_cost = fields.Float('MRM Cost')
    mrm_start_date = fields.Date('MRM Start Date')
    mrm_end_date = fields.Date('MRM End Date')

    def compute_nb_expenses(self):
        for record in self:
            record.expense_count = len(record.expense_ids)

    def show_related_expenses(self):
        ctx = {}
        ctx['default_campaign_id'] = self.id
        ctx['default_is_campaign'] = True
        return {
        "name": _("Expenses"),
        "type": 'ir.actions.act_window',
        "res_model": 'hr.expense',
        "view_mode": "tree,form",
        "domain": [('id', 'in', self.expense_ids.ids)],
        "context": ctx
        }


    def _get_child_companies(self):
        company = self.env.company
        child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
        if child_company:
            return child_company.id
        else:
            return company.id

    def compute_currency_usd(self):
        for record in self:
            record['currency_usd'] = self.env.ref('base.USD').id

    def _compute_cost_per_lead(self):
        date = datetime.now().strftime('%Y-%m-%d')
        for record in self:
            total_expense = 0
            record['cost_per_lead'] = 0
            for expense in record.expense_ids:
                total_expense += expense.currency_id._convert(expense.total_amount,self.env.ref('base.USD'),expense.company_id,date)
            record['total_expense'] = total_expense
            if record['crm_lead_count']:
                record['cost_per_lead'] = total_expense / record['crm_lead_count']

    def _compute_cost_per_acquisition(self):
        date = datetime.now().strftime('%Y-%m-%d')
        for record in self:
            total_expense = 0
            record['cost_per_acquisition'] = 0
            orders = self.env['sale.order'].search([('campaign_id','=',record.id),('state','in',['sale','done'])])
            for expense in record.expense_ids:
                total_expense += expense.currency_id._convert(expense.total_amount,self.env.ref('base.USD'),expense.company_id,date)

            if len(orders):
                record['cost_per_acquisition'] = total_expense / len(orders)

    def _compute_roi(self):
        date = datetime.now().strftime('%Y-%m-%d')
        for record in self:
            record['roi'] = 0
            total_expense = 0
            total_revenue = 0
            for expense in record.expense_ids:
                total_expense += expense.currency_id._convert(expense.total_amount,self.env.ref('base.USD'),expense.company_id,date)

            orders = self.env['sale.order'].search([('campaign_id','=',record.id),('state','in',['sale','done'])])
            for order in orders:
                total_revenue += order.currency_id._convert(order.amount_untaxed,self.env.ref('base.USD'),order.company_id,date)
            roi = total_revenue - total_expense
            if total_expense > 0:
                roi = (roi / total_expense) * 100
            if roi < 0:
                roi = 0
            record['roi'] = roi





