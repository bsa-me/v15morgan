# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseComment(models.TransientModel):
    _name = "payslip.reject.reason"
    reason = fields.Text('Reason')
    payslip_id = fields.Many2one('hr.payslip','Payslip')
    payslip_ids = fields.Many2many('hr.payslip',string='Payslips')
    def reject(self):
        self.ensure_one()
        if self.payslip_id:
        	payslip = self.payslip_id
        	payslip.sudo().write({'rejected_reason': self.reason})
        	payslip.sudo().action_payslip_cancel()

        elif self.payslip_ids:
        	for payslip in self.payslip_ids:
        		payslip.sudo().write({'rejected_reason': self.reason})
        		payslip.sudo().action_payslip_cancel()


        return True
