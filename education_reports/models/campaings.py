from odoo import api, fields, models
from datetime import datetime


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    channel_id = fields.Many2one('im_livechat.channel')
    course_profit_margin = fields.Float(string='Course Profit Margin')
    source_id = fields.Many2one('utm.source')
    medium_id = fields.Many2one('utm.medium')
    term_id = fields.Many2one('term')
    program_id = fields.Many2one('program')
    state = fields.Selection([('draft', 'New'), ('running', 'Running'), ('stopped', 'Stopped')])
    total_expense = fields.Float(string='Expenses')
    company_id = fields.Many2one(states={'refused': [('readonly', True)]},readonly=False)
    total_revenue = fields.Monetary(compute="_compute_total_revenue",currency_field='currency_usd')
    
    def _compute_total_revenue(self):
        date = datetime.now().strftime('%Y-%m-%d')
        for record in self:
            total_revenue = 0
            orders = self.env['sale.order'].search([('campaign_id','=',record.id),('state','in',['sale','done'])])
            for order in orders:
                total_revenue += order.currency_id._convert(order.amount_untaxed,self.env.ref('base.USD'),order.company_id,date)
            record['total_revenue'] = total_revenue


class MarketingCampaign(models.Model):
    _inherit = 'marketing.campaign'

    source_id = fields.Many2one('utm.source')
    medium_id = fields.Many2one('utm.medium')
