from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = ['crm.lead']
    company_id = fields.Many2one('res.company',string="Region", domain="[('is_region', '=', True)]",default=lambda self: self._get_child_companies())
    industry_id = fields.Many2one('res.partner.industry',string="Industry")
    program_id = fields.Many2one('program',string="Program")
    expiration = fields.Selection([('expired','Expired'),('not expired','Not Expired')])
    course_ids = fields.Many2many('course',string='Courses',domain="[('region_ids','in',company_id),('program_id','=',program_id)]")
    study_format = fields.Selection([('multiple','Multiple Formats'),('live','Live Class'),('liveonline','Live Online'),('self','Self-Study'),('online','Online'),('inhouse','In House'),('private','Private Tutoring'),('other','Other'),('standalone','StandAlone'),('workshop','Workshop')],string='Study Format')
    event_ids = fields.Many2many('event.event',string='Events',domain="[('company_id','=',company_id),('term_id','=',reporting_period),('program_id','=',program_id)]")
    event_id = fields.Many2one('event.event','Event',domain="[('company_id','=',company_id),('term_id','=',reporting_period),('program_id','=',program_id),('course_id','in',course_ids),('state','=','confirm')]")
    product_ids = fields.Many2many('product.template',string='Products')
    reporting_period = fields.Many2one('term','Targeted Term')
    exam_id = fields.Many2one('exam',string='Exam Window')
    factor_of_decision = fields.Many2one('factor.decision','Factor of decision')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    middle_name = fields.Char(string='Middle Name')
    program_ids = fields.Many2many('program',string='Programs')
    stage = fields.Selection([('fourtyeight','48 Hours'),('gptoweek','Up To 1 Week'),('htop1months','Up To 90 Days'),('overthree','Over 3 Months')],string='Lead Stage')
    days = fields.Integer(string='Days',compute="_compute_days")
    exam = fields.Boolean(related='company_id.exam')
    cpf = fields.Boolean(related='company_id.cpf')
    quotation_revenue = fields.Float(string='Quotation Revenue')
    simulated_revenue = fields.Float(string='Simulated Revenue')
    event_ticket_id = fields.Many2one('event.event.ticket')
    call_count = fields.Integer(compute="compute_nb_visits")
    visit_count = fields.Integer(compute="compute_nb_visits")
    call_ids = fields.One2many('calendar.event','opportunity_id',string='Office Calls',domain="[('is_call','=',True)]")
    visit_ids = fields.One2many('calendar.event','opportunity_id',string='Offline Visits',domain="[('is_visit','=',True)]")
    state = fields.Selection([('notreachable','Not Reachable'),('progress','In Progress'),('dead','Dead')])
    account_type = fields.Selection([('b2c', 'B2C'),('b2b', 'B2B'),('b2u', 'B2U')],string='Account Type', related=False)
    child_partner_id = fields.Many2one('res.partner',string='Child Contact')
    initial_status = fields.Selection([('unaware','Un-aware'),('aware','Aware'),('searching','Searching'),('decided','Decided'),('satisfied','Satisfied'),('euphoric','Euphoric')],string='Initial Status')
    crm_status_id = fields.Many2one('crm.stage.status',string='Stage Status',domain="[('stage_id','=',stage_id)]")
    parent_id = fields.Many2one('res.partner',string='Parent Company',related="partner_id.parent_id",store=True)
    stage_id = fields.Many2one(string='Opportunity Stage')
    mrm_id = fields.Integer('MRM ID')
    mrm_user = fields.Char('MRM USER')
    migration_type = fields.Selection([('opportunity', 'Opportunity'),('submission', 'Submission'),('enquiry', 'Enquiry')],string='MRM type')
    mrm_age = fields.Integer('MRM age')
    mrm_create_date = fields.Date('MRM create date')
    mrm_invoice_total = fields.Float('MRM total invoiced')
    opportunity_mrm_id = fields.Integer('MRM Opportunity ID')
    mrm_subject = fields.Char('MRM Subject')
    mrm_body = fields.Text('MRM Body')
    mrm_dead_reason = fields.Text('MRM Dead Reason')
    mrm_url = fields.Char('MRM URL')


    @api.onchange('first_name', 'last_name', 'middle_name')
    def _fill_lead_name(self):
        lead_name = ''
        if self.first_name:
            lead_name = self.first_name

        if self.first_name and self.middle_name:
            lead_name = self.first_name + ' ' + self.middle_name

        if self.first_name and self.last_name:
            lead_name = self.first_name + ' ' + self.last_name

        if self.first_name and self.last_name and self.middle_name:
            lead_name = self.first_name + ' ' + self.middle_name + ' ' + self.last_name

        return {'value': {'name': lead_name, 'contact_name': lead_name}}

    @api.onchange('company_id', 'program_id', 'study_format')
    def _clear_courses(self):
        return {'value': {'course_ids': [(5,0,0)]}}


    @api.depends('create_date')
    def _compute_days(self):
        for record in self:
            now=datetime.datetime.now()
            if(record.create_date):
                date = datetime.datetime.strptime(record.create_date, '%Y-%m-%d')
                leadDate = now - date
                record.days=leadDate.days

    @api.model
    def create(self, vals):
        record = super(CrmLead, self).create(vals)

        self.env['event.sale.forecast'].search([('opportunity_id', '=', record.id)]).unlink()
        expectedRevenue = 0
        #Get All Events
        for event in record.event_ids:
            event_price = 0
            if event.event_ticket_ids:
                for ticket in event.event_ticket_ids:
                    event_price += ticket.price
                event_price = event_price / len(event.event_ticket_ids)

            self.env['event.sale.forecast'].create({
                'event_id': event.id,
                'opportunity_id': record.id,
                'partner_id': record.partner_id.id if record.partner_id else False,
                'price_unit': event_price,
                'probability': record.probability,
                'amount': event_price * (record.probability / 100)
                })

        record['simulated_revenue'] = (record.expected_revenue * record.probability)/100


        return record

    def _get_child_companies(self):
        company = self.env.company
        child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
        if child_company:
            return child_company.id
        else:
            return company.id

    @api.onchange('email_from')
    def _onchange_email(self):
        if self.email_from:
            if self.type == 'opportunity':
                partner = self.env['res.partner'].search([('email','=',self.email_from)],limit=1)
                if partner:
                    self.partner_id = partner.id
                    #self._onchange_partner_id()


    def compute_nb_visits(self):
        for record in self:
            calls = self.env['calendar.event'].search([('opportunity_id','=',record.id),('is_call','=',True)])
            visits = self.env['calendar.event'].search([('opportunity_id','=',record.id),('is_visit','=',True)])
            record['call_count'] = len(calls)
            record['visit_count'] = len(visits)


    def show_related_calls(self):
        calls = self.env['calendar.event'].search([('opportunity_id','=',self.id),('is_call','=',True)])
        res = {
        'type': 'ir.actions.act_window',
        'name': _('Calls'),
        'view_mode': 'tree,form',
        'res_model': 'calendar.event',
        'domain' : [('id','in',calls.ids)],
        'target': 'current',
        'context': {'default_opportunity_id': self.id, 'default_is_call': True, 'form_view_ref': 'education.calendar_event_call_vist_form'}
        }

        return res

    def show_related_visits(self):
        visits = self.env['calendar.event'].search([('opportunity_id','=',self.id),('is_visit','=',True)])
        res = {
        'type': 'ir.actions.act_window',
        'name': _('Offline visits'),
        'view_mode': 'tree,form',
        'res_model': 'calendar.event',
        'domain' : [('id','in',visits.ids)],
        'target': 'current',
        'context': {'default_opportunity_id': self.id, 'default_is_visit': True, 'form_view_ref': 'education.calendar_event_call_vist_form'}
        }

        return res

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            if self.partner_id.industry_id:
                self.industry_id = self.partner_id.industry_id.id


    @api.onchange('child_partner_id')
    def onchange_child_partner(self):
        if self.child_partner_id:
            self.contact_name = self.child_partner_id.name
            self.title = self.child_partner_id.title.id
            self.function = self.child_partner_id.function
            self.mobile = self.child_partner_id.mobile
            self.partner_name = self.partner_id.child_partner_id.name
            self.street = self.child_partner_id.street
            self.street2 = self.child_partner_id.street2
            self.city = self.child_partner_id.city
            self.state_id = self.child_partner_id.state_id.id
            self.country_id = self.child_partner_id.country_id.id

        else:
            contact_name = self.title = self.function = self.mobile = self.partner_name = self.street = self.street2 = self.city = self.state_id = self.country_id = False

    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        res = super(CrmLead, self)._create_lead_partner_data(name, is_company, parent_id)
        res['account_type'] = 'b2b' if is_company else 'b2c'
        return res
