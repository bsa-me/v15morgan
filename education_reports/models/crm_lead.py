from odoo import fields, models


class Lead(models.Model):
    _inherit = 'crm.lead'
    company_id = fields.Many2one(string='Region')
    account_type = fields.Selection([('b2c', 'B2C'),('b2b', 'B2B'),('b2u', 'B2U')],string='Account Type', related=False,store=True)

    def compute_total_revenue(self):
        for rec in self:
            rec.invoiced_amount = rec.campaign_id.invoiced_amount

    def compute_total_ad_cost(self):
        for rec in self:
            rec.total_ad_cost = sum(rec.campaign_id.expense_ids.mapped('total_amount'))

    def compute_conversion_rate(self):
        for rec in self:
            sale_order_nb = len(rec.order_ids.filtered(lambda line: line.state == 'sale'))
            if rec.campaign_id.crm_lead_count != 0:
                rec.conversion_rate = (sale_order_nb / rec.campaign_id.crm_lead_count) * 100
            else:
                rec.conversion_rate = 0

    def compute_lead_count(self):
        for rec in self:
            rec.lead_count = rec.campaign_id.crm_lead_count

    total_ad_cost = fields.Float(string='Total Ad Cost', compute='compute_total_ad_cost', store=True)
    invoiced_amount = fields.Integer(string='Total Revenue', compute='compute_total_revenue', store=True)
    cost_per_lead = fields.Float(related='campaign_id.cost_per_lead')
    cost_per_acquisition = fields.Float(related='campaign_id.cost_per_acquisition')
    conversion_rate = fields.Float(string='Conversion Rate %', compute='compute_conversion_rate', store=True)
    roi = fields.Float(related='campaign_id.roi')
    lead_count = fields.Float(string='Lead Count', compute='compute_lead_count', store=True)


class Exam(models.Model):
    _inherit = 'exam'

    active = fields.Boolean(default=True)
