from odoo import models, fields,api,_
from datetime import date
from odoo.osv import expression
from odoo.exceptions import ValidationError


class Employees(models.Model):
    _inherit = "hr.employee"
    company_id = fields.Many2one('res.company', sting="Company")
    medic_exam = fields.Date('Medical Exam')
    vehicle = fields.Char('Company Vehicle')
    vehicle_distance = fields.Integer(string="Home-Work Dist.")
    place_of_birth = fields.Char('Place of Birth')
    manager = fields.Boolean('Is a Manager')
    resource_calendar_id = fields.Many2one('resource.calendar', string="Working Hours")
    course_ids = fields.Many2many('course', compute="_compute_courses", store=True)
    is_instructor = fields.Boolean()
    joining_date = fields.Date('Joining Date',compute="_compute_joining_date")
    instructor_status = fields.Selection([('draft','Potential'),('active','Active'),('dormant','Dormant'),('suspended','Suspended')],compute="_compute_status",store=True, default='draft')
    social_twitter = fields.Char('Twitter Account')
    social_facebook = fields.Char('Facebook Account')
    social_linkedin = fields.Char('LinkedIn Account')
    social_youtube = fields.Char('Youtube Account')
    social_instagram = fields.Char('Instagram Account')
    biography = fields.Html('Biography')
    instructor_job_position = fields.Char()
    age_group = fields.Selection([('18-21','18-21'),('22-25','22-25'),('25-29','25-29'),('30-35','30-35'),('35-45','35-45'),('45above','45 and above')], string="Age Group")
    is_student = fields.Boolean('Ex student',compute="_compute_student")
    registration_number = fields.Char(company_dependent=True,string='Tax Registration Number')
    document_ids = fields.One2many('documents.document','employee_id',string='Documents')
    document_count = fields.Integer(compute="compute_document_count",related=False)
    folder_id = fields.Many2one('documents.folder',string='Workspace')
    recruiting_city_id = fields.Many2one('res.company',domain="[('is_region','=',True)]",string='Recruiting City')
    contract_company_ids = fields.Many2many('res.company',string='Contract Companies')
    payment_method = fields.Selection([('cash', 'Cash'),('cheque', 'Cheque'),('credit_card', 'Credit Card'), ('transfer', 'Transfer')],string='Payment Method')
    survey_ids = fields.One2many('survey.survey','instructor_id',string='Surveys')
    mobile = fields.Char('Mobile')
    session_ids = fields.One2many('event.track','employee_id',string='Sessions')
    mrm_id = fields.Integer('MRM ID')
    mrm_status = fields.Char()
    tfrm_id = fields.Integer('TFRM ID')
    

    def show_related_documents(self):
        ctx = {}
        ctx['default_employee_id'] = self.id
        ctx['default_folder_id'] = self.folder_id.id if self.folder_id else False
        res = {
        'type': 'ir.actions.act_window',
        'name': _('Documents'),
        'view_mode': 'tree,kanban,form',
        'res_model': 'documents.document',
        'domain': [('id','in',self.document_ids.ids)],
        'target': 'current',
        'context': ctx,
        }

        return res

    @api.model
    def create(self, vals):
        record = super(Employees, self).create(vals)

        record['folder_id'] = self.env['documents.folder'].create({'name': vals['name']}).id

        return record

    def write(self, vals):
        courses = []
        companies = []
        for contract in self.contract_ids:
            if(contract.course_ids and contract.state == 'open'):
                for course in contract.course_ids:
                    courses.append(course.id)

        if courses:
                vals['course_ids'] = [(6,0,courses)]
            
        else:
            vals['course_ids'] = [(5,0,0)]

        for contract in self.contract_ids:
            if contract.state == 'open':
                companies.append(contract.company_id.id)

        if companies:
            vals['contract_company_ids'] = [(6,0,companies)]

        else:
            vals['contract_company_ids'] = [(6,0,courses)]
        
        return super(Employees, self).write(vals)

    def compute_document_count(self):
        for record in self:
            record['document_count'] = len(record.document_ids)

    def _compute_courses(self):
        for record in self:
            courses = []
            for contract in record.contract_ids:
                if(contract.course_ids and contract.state == 'open'):
                    for course in contract.course_ids:
                        courses.append(course.id)
            if(courses):
                record.course_ids=[(6,0,courses)]
            else:
                record.course_ids = [(5,0,0)]


    def _compute_joining_date(self):
        for record in self:
            first_contract = self.env['hr.contract'].search([('employee_id','=',record.id)],order="date_start asc",limit=1)
            if first_contract:
                record['joining_date'] = first_contract.date_start

            else:
                record['joining_date'] = False

    
    @api.depends('active', 'contract_ids')
    def _compute_status(self):
        for record in self:
            instructor_status = False
            if not record.active:
                instructor_status = 'suspended'


            elif not record.contract_ids:
                instructor_status = 'draft'

            else:
                open_contract = self.env['hr.contract'].search([('employee_id','=',record.id),('state','=','open')],limit=1)
                if open_contract:
                    instructor_status = 'active'

                else:
                    states = []
                    contracts = self.env['hr.contract'].search([('employee_id','=',record.id)])
                    for contract in contracts:
                        states.append(contract.state)

                    if 'cancel' in states or 'close' in states:
                        instructor_status = 'dormant'

                    else:
                        instructor_status = 'draft'

            record.instructor_status = instructor_status

    @api.onchange('address_id')
    def _onchange_address(self):
        if not self.is_instructor:
            self.work_phone = self.address_id.phone
            self.mobile_phone = self.address_id.mobile
        else:
            self.work_phone = False
            self.mobile_phone = False

    def _compute_student(self):
        for record in self:
            record.is_student = False
            if record.address_home_id:
                invoices = self.env['account.move'].search([('partner_id','=',record.address_home_id.id),('invoice_date','<',record.create_date),('state','=','posted')])
                if invoices:
                    record.is_student = True


    @api.onchange('birthday')
    def onchange_birthday(self):
        today = date.today()
        if self.birthday:
            age = today.year - self.birthday.year - ((self.birthday.month, today.day) < (self.birthday.month, self.birthday.day))
            age_group = '18-21'
            if age >=18 and age <= 21:
                age_group = '18-21'

            elif age > 21 and age <= 25:
                age_group = '22-25'

            elif age > 25 and age <= 29:
                age_group = '25-29'

            elif age > 30 and age <= 35:
                age_group = '30-35'

            elif age > 35 and age <= 45:
                age_group = '35-45'

            elif age > 45:
                age_group = '45above'

            self.age_group = age_group


    @api.onchange('country_id')
    def onchange_country(self):
        if self.country_id:
            if self.country_id.phone_code:
                self.work_phone = '+' + str(self.country_id.phone_code) + ' '
                self.mobile_phone = '+' + str(self.country_id.phone_code) + ' '

    def unlink(self):
        if self.document_ids:
            self.document_ids.unlink()
        if self.folder_id:
            self.folder_id.unlink()
        rec = super(Employees, self).unlink()
        return rec

    def _get_company_contracts(self, date_from, date_to, company, states=['open'], kanban_state=False):
        state_domain = [('state', 'in', states)]
        if kanban_state:
            state_domain = expression.AND([state_domain, [('kanban_state', 'in', kanban_state)]])

        return self.env['hr.contract'].search(
            expression.AND([[('employee_id', 'in', self.ids)],
                state_domain,
                [('date_start', '<=', date_to),('company_id', '=', company.id),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', date_from)]]))



class PublicEmloyee(models.Model):
    _inherit = "hr.employee.public"
    vehicle_distance = fields.Integer(string="Home-Work Dist.")
    manager = fields.Boolean('Is a Manager')
    is_instructor = fields.Boolean()
    instructor_status = fields.Selection([('draft','Potential'),('active','Active'),('dormant','Dormant'),('suspended','Suspended')], default='draft')
    social_twitter = fields.Char('Twitter Account')
    social_facebook = fields.Char('Facebook Account')
    social_linkedin = fields.Char('LinkedIn Account')
    social_youtube = fields.Char('Youtube Account')
    social_instagram = fields.Char('Instagram Account')
    biography = fields.Html('Biography')
    instructor_job_position = fields.Char()
    age_group = fields.Selection([('18-21','18-21'),('22-25','22-25'),('25-29','25-29'),('30-35','30-35'),('35-45','35-45'),('45above','45 and above')], string="Age Group")
    registration_number = fields.Char(company_dependent=True,string='Tax Registration Number')
    payment_method = fields.Selection([('cash', 'Cash'),('cheque', 'Cheque'),('credit_card', 'Credit Card'), ('transfer', 'Transfer')],string='Payment Method')
    mobile = fields.Char('Mobile')
    folder_id = fields.Many2one('documents.folder',string='Workspace')
    recruiting_city_id = fields.Many2one('res.company',domain="[('is_region','=',True)]",string='Recruiting City')
    










