# -*- coding: utf-8 -*-

import datetime
from dateutil import parser
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
import calendar

class AccountPaymentTermLine(models.Model):
  _inherit='account.payment.term.line'

  option = fields.Selection([
    ('day_after_invoice_date', "days after the invoice date"),
    ('day_following_month', "of the following month"),
    ('day_current_month', "of the current month"),
    ('day_before_start_date_event','day_before_start_date_event'),
    ('day_after_end_date_event','Day(s) after the end date of the event'),


    ],
    default='day_after_invoice_date', required=True, string='Options'
    )

  """def get_fp_date(self,inv_date=False):
    date = False
    date_of_invoice = datetime.datetime.now().strftime('%Y-%m-%d')
    if self.option:
        if(inv_date):
            date_of_invoice = inv_date

        if(self.option == 'day_after_invoice_date'):
            invoice_date = datetime.datetime.strptime(date_of_invoice, '%Y-%m-%d')
            days = datetime.timedelta(days=self.days)
            date = (invoice_date + days).date()

        elif(self.option == 'fix_day_following_month'):
            invoice_date = datetime.datetime.strptime(date_of_invoice, '%Y-%m-%d')
            invoice_month = datetime.datetime.strftime(invoice_date, '%m')
            invoice_year = datetime.datetime.strftime(invoice_date, '%Y')
            invoice_days = datetime.datetime.strftime(invoice_date, '%d')
            last_day = calendar.monthrange(int(invoice_year),int(invoice_month))[1]
            days = datetime.timedelta(days=int(last_day) - int(invoice_days))
            month_date = (invoice_date + days).date()
            date = month_date + timedelta(days=int(self.days))

        elif(self.option == 'last_day_following_month'):
            invoice_date = datetime.datetime.strptime(date_of_invoice, '%Y-%m-%d')
            invoice_month = datetime.datetime.strftime(invoice_date, '%m')
            invoice_year = datetime.datetime.strftime(invoice_date, '%Y')
            invoice_days = datetime.datetime.strftime(invoice_date, '%d')
            last_day = calendar.monthrange(int(invoice_year),int(invoice_month)+1)[1]
            days = datetime.timedelta(days=int(last_day) - int(invoice_days))
            date = (invoice_date + days).date()
            date = date + relativedelta(months=1)

        elif(self.option == 'last_day_current_month'):
            invoice_date = datetime.datetime.strptime(date_of_invoice, '%Y-%m-%d')
            invoice_month = datetime.datetime.strftime(invoice_date, '%m')
            invoice_year = datetime.datetime.strftime(invoice_date, '%Y')
            invoice_days = datetime.datetime.strftime(invoice_date, '%d')
            last_day = calendar.monthrange(int(invoice_year),int(invoice_month))[1]
            days = datetime.timedelta(days=int(last_day) - int(invoice_days))
            date = (invoice_date + days).date()
    
    return date"""
    
  
