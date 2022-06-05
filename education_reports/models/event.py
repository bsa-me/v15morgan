from odoo import api, fields, models
from datetime import datetime


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    def _compute_last_authentication(self):
        for rec in self:
            if rec.partner_id:
                rec.last_logged_in = rec.partner_id.user_id.login_date

    def _compute_access_create_on(self):
        for rec in self:
            if rec.partner_id:
                rec.access_create_on = rec.partner_id.user_id.create_date

    def _compute_amount_paid_percentage(self):
        for rec in self:
            total_invoiced = 0
            total_amount = 0
            for invoice in rec.sale_order_id.invoice_ids:
                total_amount += invoice.amount_total
                total_paid = invoice.amount_total - invoice.amount_residual
                total_invoiced += total_paid
            if total_amount > 0:
                rec.amount_paid_percentage = (total_invoiced * 100) / total_amount
            if rec.amount_paid_percentage < 0:
                rec.amount_paid_percentage = 0

    # def compute_total_revenue(self):
    #     for record in self:
    #         totalRevenue = 0
    #         revenues = self.env['sale.order.line'].search([('event_id', '=', record.event_id.id)])
    #         for revenue in revenues:
    #             date = revenue.order_id.date_order if revenue.order_id.date_order else datetime.now().strftime(
    #                 '%Y-%m-%d')
    #             amount_revenue = revenue.price_unit * revenue.product_uom_qty
    #             amount = revenue.order_id.currency_id._convert(amount_revenue, self.env.ref('base.USD'),
    #                                                            revenue.order_id.company_id, date)
    #             totalRevenue += amount
    #
    #         record['total_revenue'] = totalRevenue

    # def compute_total_expenses(self):
    #     for record in self:
    #         totalExpense = 0
    #         expenses = self.env['hr.expense'].search([('event_id', '=', record.event_id.id)])
    #         for expense in expenses:
    #             date = expense.date if expense.date else datetime.now().strftime('%Y-%m-%d')
    #             amount_expense = totalExpense + expense.unit_amount
    #             amount = expense.currency_id._convert(amount_expense, self.env.ref('base.USD'), expense.company_id,
    #                                                   date)
    #             totalExpense += amount
    #
    #         record['total_expenses'] = totalExpense

    # def compute_total_instructor_rates(self):
    #     for record in self:
    #         total = 0
    #         for instructor in record.event_id.organizer_ids:
    #             attendances = self.env['hr.attendance'].search([('employee_id', '=', instructor.id)])
    #             for attendance in attendances:
    #                 date = attendance.check_in.date()
    #                 session = attendance.session_id
    #                 worked_days = self.env['hr.payslip.worked_days'].search(
    #                     [('session_id', '=', session.id), ('session_id.event_id', '=', record.event_id.id),
    #                      ('payslip_id.state', 'in', ['accountingapproval', 'verify', 'done'])])
    #                 for day in worked_days:
    #                     amount = day.contract_currency_id._convert(day.amount, self.env.ref('base.USD'),
    #                                                                day.payslip_id.company_id, date)
    #                     total = total + amount
    #
    #         record['total_instructor_rates'] = total

    # def compute_total(self):
    #     for record in self:
    #         record['total'] = record.total_revenue - (record.total_expenses + record.total_instructor_rates)

    amount_paid_percentage = fields.Float(compute='_compute_amount_paid_percentage', store=True,
                                          string='% Amount paid from invoice')

    access_create_on = fields.Datetime(string='Access Create On', compute='_compute_access_create_on', store=True)
    last_logged_in = fields.Datetime(string='Last logged in', compute='_compute_last_authentication', store=True)
    # total_revenue = fields.Float('Total Revenue', compute="compute_total_revenue", store=True)
    # total_expenses = fields.Float('Total Expenses', compute="compute_total_expenses", store=True)
    # total_instructor_rates = fields.Float(string='Total Instructor Rates', compute="compute_total_instructor_rates",
    #                                       store=True)
    # total = fields.Float('Total', compute="compute_total", store=True)
    #


class EventTrack(models.Model):
    _inherit = 'event.track'

    event_type_id = fields.Many2one(related='event_id.event_type_id', store=True)


class Event(models.Model):
    _inherit = 'event.event'

    event_sales_ids = fields.One2many('event.sales', 'event_id', string='Event Sales')

    def _status_count(self):
        for rec in self:
            rec.nb_confirmed = rec.registration_ids.mapped('state').count('open')
            rec.nb_unconfirmed = rec.registration_ids.mapped('state').count('draft')
            rec.nb_active = rec.registration_ids.mapped('transfer_status').count('active')
            rec.nb_drop = rec.registration_ids.mapped('transfer_status').count('dropout')
            rec.nb_transferred = rec.registration_ids.mapped('transfer_status').count('transferred')
            if rec.nb_confirmed > 0:
                rec.percentage_dropout = (rec.nb_drop / rec.nb_confirmed) * 100
                rec.percentage_transferred = (rec.nb_transferred / rec.nb_confirmed) * 100

    nb_confirmed = fields.Integer(string='# of confirmed', compute='_status_count', store=True)
    nb_unconfirmed = fields.Integer(string='# of unconfirmed', compute='_status_count', store=True)
    nb_active = fields.Integer(string='# of active', compute='_status_count', store=True)
    nb_drop = fields.Integer(string='# of drop outs', compute='_status_count', store=True)
    nb_transferred = fields.Integer(string='# of transferred', compute='_status_count', store=True)
    percentage_dropout = fields.Float(string='% of drop out', compute='_status_count', store=True)
    percentage_transferred = fields.Float(string='% of Transferred', compute='_status_count', store=True)
