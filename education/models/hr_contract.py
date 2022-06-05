from odoo import models, fields , api
from odoo.exceptions import ValidationError
from datetime import datetime


class EmployeeContract(models.Model):
    _inherit = 'hr.contract'
    program_id = fields.Many2one('program', string="Program", required="1")
    course_id = fields.Many2one('course', string = "Course", required=False)
    course_ids = fields.Many2many('course',string="Courses",required=1)
    event_type_id = fields.Many2one('event.type', string="Event Type")
    partner_id = fields.Many2one('res.partner', string = "Account")
    display_partner_id = fields.Boolean('Display Account', compute='_compute_display_parter_id')
    signed_agreement = fields.Many2one('documents.document', string="Signed Agreement")
    first_session_id = fields.Many2one('event.track',string='First session',compute="_compute_session")
    company_id = fields.Many2one(string="Region", domain="[('is_region', '=', True)]",default=lambda self: self._get_child_companies())
    currency_usd = fields.Many2one('res.currency',compute="_compute_usd")
    usd_wage = fields.Float("Wage ($)")
    is_global = fields.Boolean()
    iht_event_id = fields.Many2one('event.event',domain="[('event_type_id','=',event_type_id),('state','=','confirm'),('course_id','in',course_ids),('partner_id','=',partner_id)]",string="IHT Event")

    def _compute_usd(self):
      for record in self:
        record['currency_usd'] = self.env.ref('base.USD').id
    
    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        for contract in self.filtered(lambda c: c.state not in ['draft', 'cancel'] or c.state == 'draft' and c.kanban_state == 'done'):
            return True
    
    @api.onchange('event_type_id')
    def _onchange_event_type_id(self):
        val = {}
        if(self.event_type_id.study_format == 'inhouse'):
          val['value'] = {'display_partner_id': True}
        else:
          val['value'] = {'display_partner_id': False}
        return val

        
    def _compute_display_parter_id(self):
        for record in self:
            if(record.event_type_id.study_format == 'inhouse'):
              record.display_partner_id = True
            else:
              record.display_partner_id = False
              
    @api.onchange('employee_id','program_id','date_start')
    def _onchange_name(self):
      if (self.employee_id and self.program_id and self.date_start):
        if (self.partner_id):
          self.name = self.partner_id.name + ' - ' + self.employee_id.name + ' - '+ self.program_id.name + ' - ' + self.date_start.strftime('%d %B %Y')
        else:
          self.name = self.employee_id.name + ' - '+ self.program_id.name + ' - ' + self.date_start.strftime('%d %B %Y')


    def compute_courses(self, employee_id):	
      contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee_id.id),('state','=','open'),('course_ids','!=',False)])	
      courses = contract_ids.mapped('course_ids')
      return courses

    @api.model	
    def create(self, vals):
      date = datetime.now().strftime('%Y-%m-%d')
      record = super(EmployeeContract, self).create(vals)	
      employee_id = self.env['hr.employee'].browse(vals.get('employee_id'))
      courses = record.course_ids

      if courses:
        if not record.iht_event_id:
          if not record.is_global:
            sessions = self.env['event.track'].search(['|',('event_id.company_id','=',record.company_id.id),('event_id.is_global','=',True),('event_id.course_id','in',courses.ids),('event_id.state','=','confirm')])
          else:
            sessions = self.env['event.track'].search([('event_id.course_id','in',courses.ids),('event_id.state','=','confirm')])

        else:
          sessions = self.env['event.track'].search([('event_id','=',record.iht_event_id.id)])


        if 'course_ids' in vals:
            employee_id._compute_courses()
            for session in sessions:
                session._compute_instructors()


      if 'signed_agreement' in vals:
        agreement = self.env['documents.document'].browse(vals['signed_agreement']).write({'folder_id': employee_id.folder_id.id, 'employee_id': employee_id.id})


      wage = record.hourly_wage
      if 'hourly_wage' in vals:
        wage = vals['hourly_wage']

      company = record.company_id
      if 'company_id' in vals:
        company = self.env['res.company'].browse(vals['company_id'])


      usd_wage = company.currency_id._convert(wage,self.env.ref('base.USD'),company,date)
      record['usd_wage'] = usd_wage

      employee_id._compute_status()
      return record
    
    def write(self, vals):
      date = datetime.now().strftime('%Y-%m-%d')
      employee_id = self.employee_id
      if 'employee_id' in vals:
        employee_id = self.env['hr.employee'].browse(vals.get('employee_id'))

      is_global = self.is_global
      if 'is_global' in vals:
        is_global = vals['is_global']


      wage = self.hourly_wage
      if 'hourly_wage' in vals:
        wage = vals['hourly_wage']

      company = self.company_id
      if 'company_id' in vals:
        company = self.env['res.company'].browse(vals['company_id'])

      iht_event_id = self.iht_event_id.id
      if 'iht_event_id' in vals:
        iht_event_id = vals['iht_event_id']
      
      
      if company:
        usd_wage = company.currency_id._convert(wage,self.env.ref('base.USD'),company,date)
        vals['usd_wage'] = usd_wage

      employee_id._compute_status()
      res = super(EmployeeContract, self).write(vals)
      courses = self.course_ids
      sessions = False
      if courses:
        if not self.iht_event_id:
          if not is_global:
            sessions = self.env['event.track'].search(['|','|',('event_id.company_id','=',company.id),('event_id.company_id','in',company.region_ids.ids),('event_id.is_global','=',True),('event_id.course_id','in',courses.ids),('event_id.state','=','confirm'),('stage_id.name','=','Pending')])
          else:
            sessions = self.env['event.track'].search([('event_id.course_id','in',courses.ids),('event_id.state','=','confirm'),('stage_id.name','=','Pending')])
        
        else:
          sessions = self.env['event.track'].search([('event_id','=',iht_event_id)])


      #if 'course_ids' in vals:
      employee_id._compute_courses()
      if sessions:
        for session in sessions:
          session._compute_instructors()
      
      return res


    @api.onchange('employee_id','program_id','course_ids')
    def onchange_start_date(self):
      if self.employee_id and self.course_ids and self.program_id:
        first_session = self.env['event.track'].search([('employee_id','=',self.employee_id.id),('course_id','in',self.course_ids.ids)],limit=1,order='date asc')
        if first_session:
          self.date_start = first_session.date

        else:
          self.date_start = False

    @api.onchange('program_id')
    def onchange_program(self):
      if self.program_id:
        self.course_ids = False
        self.date_start = False


    def _compute_session(self):
      for record in self:
        record['first_session_id'] = False
        first_session = self.env['event.track'].search([('employee_id','=',record.employee_id.id),('course_id','in',record.course_ids.ids)],limit=1,order='date asc')
        if first_session:
          record['first_session_id'] = first_session.id

    def _get_child_companies(self):
        company = self.env.company
        child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
        if child_company:
            return child_company.id
        else:
            return company.id



    @api.constrains('hourly_wage')
    def _check_hourly_Wage(self):
        if self.hourly_wage <= 0:
            raise ValidationError("Contract Wage should be positive!")



