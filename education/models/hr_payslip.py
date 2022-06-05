from odoo import models, fields,api,_
from odoo.exceptions import UserError
from odoo.tools import date_utils
from datetime import datetime, timedelta
import re


class Payslip(models.Model):
    _inherit = 'hr.payslip'
    journal_id = fields.Many2one(related=False,store=True,domain="[('company_id', '=', company_id),('type','=','bank')]")
    company_id = fields.Many2one(string="Region", domain="[('is_region', '=', True)]",default=False)
    state = fields.Selection([('draft', 'Draft'),('operationapproval', "Operation Approval"),('accountingapproval', "Approved by Operations"),('verify', 'Waiting Payment'),('cancel', 'Rejected'),('done', 'Paid')], string='Status', index=True, readonly=True, copy=False, default='draft',help=False)
    rejected_reason = fields.Text('Reject Reason',required=False)
    parent_id = fields.Many2one('res.company',related='company_id.parent_id')
    contract_ids = fields.Many2many('hr.contract',string='Contracts',domain="['|',('company_id','=',company_id),('company_id','=',parent_id),('employee_id','=',employee_id),('date_start','<=',date_to),'|',('date_end','>=',date_from),('date_end','=',False),('state','=','open')]")
    employee_id = fields.Many2one(domain="['|', '|', ('company_id', '=', False), ('company_id', '=', company_id),('company_id', '=', parent_id)]")

    @api.onchange('contract_ids')
    def _onchange_contracts(self):
        if self.contract_ids:
            contract = str(self.contract_ids[0].id)
            contract_id = int(re.search(r'\d+', contract).group())
            self.contract_id = self.contract_ids[0].id 
            courses = self.contract_ids.mapped('course_ids').ids
            payslip_lines = self.worked_days_line_ids.filtered(lambda l: l.session_id.event_id.course_id.id not in courses and l.display_type != 'line_section').unlink()

        else:
            self.contract_id = False
            self.struct_id = False


    def submit_payslip(self):
        self.ensure_one()
        self.env['mail.activity'].sudo().search([('res_id','=',self.id),('res_model','=','hr.payslip')]).action_done()
        activity = self.env.ref('education.operation_approval')
        days = activity.delay_count
        currentDate = datetime.now().date()
        dueDate = currentDate + timedelta(days=days)
        user_id = False
        group = self.env.ref('education.class_room_department_group')
        """for user in group.users:
            #user_id = user.id
            user_id = user.id
            break
        newActivity = self.env['mail.activity'].sudo().create({
            'activity_type_id': activity.id,
            'date_deadline': dueDate,
            'user_id': user_id,
            'res_id': self.id,
            'res_model_id': self.env.ref('hr_payroll.model_hr_payslip').id,
            'res_model': 'hr.payslip',
            'res_name': self.name,
            })"""

        self.write({'state': 'operationapproval'})

    def operation_approve(self):
        self.ensure_one()
        self.env['mail.activity'].sudo().search([('res_id','=',self.id),('res_model','=','hr.payslip')]).action_done()
        activity = self.env.ref('education.accounting_approval')
        days = activity.delay_count
        currentDate = datetime.now().date()
        dueDate = currentDate + timedelta(days=days)
        user_id = False
        group = self.env.ref('education.accounting_management')
        """for user in group.users:
            #user_id = user.id
            user_id = user.id
            break
        newActivity = self.env['mail.activity'].sudo().create({
            'activity_type_id': activity.id,
            'date_deadline': dueDate,
            'user_id': user_id,
            'res_id': self.id,
            'res_model_id': self.env.ref('hr_payroll.model_hr_payslip').id,
            'res_model': 'hr.payslip',
            'res_name': self.name,
            })"""

        self.write({'state': 'accountingapproval'})


    def accounting_approve(self):
        self.ensure_one()
        self.env['mail.activity'].sudo().search([('res_id','=',self.id),('res_model','=','hr.payslip')]).action_done()
        self.write({'state': 'verify'})
        #return self.action_payslip_done()

    def return_payslip(self):
        self.ensure_one()
        self.env['mail.activity'].sudo().search([('res_id','=',self.id),('res_model','=','hr.payslip')]).action_done()
        activity = False
        state = False
        if self.state == 'operationapproval':
            state = 'draft'
            activity = self.env.ref('education.check_rejection')

        elif self.state == 'accountingapproval':
            state = 'operationapproval'
            activity = self.env.ref('education.operation_approval')
        
        days = activity.delay_count
        currentDate = datetime.now().date()
        dueDate = currentDate + timedelta(days=days)
        user_id = False
        activity = self.env.ref('education.operation_approval')
        """for user in group.users:
            #user_id = user.id
            user_id = self.env.ref('base.user_admin').id
            break
        newActivity = self.env['mail.activity'].sudo().create({
            'activity_type_id': activity.id,
            'date_deadline': dueDate,
            'user_id': user_id,
            'res_id': self.id,
            'res_model_id': self.env.ref('hr_payroll.model_hr_payslip').id,
            'res_model': 'hr.payslip',
            'res_name': self.name,
            })"""

        self.write({'state': state})



    def _get_worked_day_lines(self):
        res = []
        self.ensure_one()
        courses = self.contract_ids.mapped('course_ids')
        attendances = self.env['hr.attendance'].search(['|',('session_id.event_id.is_global','=',True),('session_id.event_id.company_id','=',self.company_id.id),('employee_id','=',self.employee_id.id),('session_id.is_paid','=',False),('session_id.event_id.course_id','in',courses.ids),('check_in','>=',self.date_from),('check_out','<=',self.date_to)])
        first_sequence = 0
        session_to_generate = 0
        

        for attendance in attendances:
            courseName = False
            diff = attendance.check_out - attendance.check_in
            days, seconds = diff.days, diff.seconds
            hours = days * 24 + seconds
            hours = hours / 3600
            session = attendance.session_id
            if not session.is_payslip_generated:
                session_to_generate += 1


            course = session.course_id
            amount = 0

            section_line = {
            'sequence': first_sequence,
            'display_type': 'line_section',
            'name': course.name,
            }

            if not section_line in res and session_to_generate > 0:
                res.append(section_line)

            else:
                courseName = section_line.get('name')

            contracts = self.env['hr.contract'].search([('course_ids','in',course.id),('employee_id','=',self.employee_id.id),('state','=','open'),('id','in',self.contract_ids.ids)])
            if contracts:
                for contract in contracts:
                    amount = contract.hourly_wage * hours
                    contract = contract.id

                    attendance_line = {
                    'sequence': (first_sequence + 1) if courseName == course.name else 0,
                    'work_entry_type_id': self.env.ref('hr_work_entry.work_entry_type_attendance').id,
                    'date': attendance.check_in,
                    'contract_id': contract,
                    'name': session.name,
                    'number_of_hours': hours,
                    'amount': amount,
                    'session_id': session.id
                    }
                    if not session.is_payslip_generated:
                        res.append(attendance_line)
        
        return res




    @api.onchange('company_id')
    def onchange_company(self):
        if self.company_id:
            payslip_journal = self.env['account.journal'].search([('company_id','=',self.company_id.id),('type','=','bank'),('name','=','Instructor Payments')],limit=1)
            if payslip_journal:
                self.journal_id = payslip_journal.id

    def _get_child_companies(self):
        company = self.env.company
        child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
        if child_company:
            return child_company.id
        else:
            return company.id

    @api.onchange('employee_id', 'struct_id', 'date_from', 'date_to','company_id')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        payslip_name = self.struct_id.payslip_name or _('Pay Slip')
        self.name = '%s - %s' % (payslip_name, self.employee_id.name or '')
        

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _("This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        else:
            self.warning_message = False

        contracts = []
        attendances = self.env['hr.attendance'].search([('employee_id','=',self.employee_id.id)])
        for attendance in attendances:
            employee_contracts = self.env['hr.contract'].search(['|','|',('company_id','=',self.company_id.id),('company_id','=',self.company_id.parent_id.id),('is_global','=',True),('course_ids','in',attendance.session_course.ids),('employee_id','=',self.employee_id.id),('course_ids','in',self.employee_id.course_ids.ids)])
            if employee_contracts:
                for contract in employee_contracts:
                    contracts.append(contract.id)

        self.contract_ids = [(6, 0, contracts)]
        

        self.worked_days_line_ids = self._get_new_worked_days_lines()

    @api.onchange('contract_ids')
    def _on_change_contract_ids(self):
        self.worked_days_line_ids = self._get_new_worked_days_lines()

    def compute_sheet(self):
        for payslip in self.filtered(lambda slip: slip.state not in ['cancel', 'done']):
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            payslip.line_ids.unlink()
            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'compute_date': fields.Date.today()})

        return True
    
