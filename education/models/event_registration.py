from odoo import  fields, models,api, _
from odoo.exceptions import UserError


class EventRegistration(models.Model):
    _inherit = 'event.registration'
    attempt_ids = fields.One2many('attempt','registration_id',string="Attempts", domain=lambda self:[('type','=','attempt')])
    attempt_exam_ids = fields.One2many('attempt','registration_id',string="Attempts", domain=lambda self:[('type','=','examhomework')])
    session_id = fields.Many2one('event.track', string='Session', required=False)
    attempt_date = fields.Date('Attempt Date')
    passing_status = fields.Selection(
        [
        ('passed', 'Passed'),
        ('failed', 'Failed')
        ],
        string='Passing Status')
    score = fields.Float('Score')
    event_id = fields.Many2one(track_visibility='onchange',required=False)
    attendance_ids = fields.One2many('attendance','registration_id',string='Attendances')
    transfer_status = fields.Selection([('draft','Draft'),('active', 'Active'),('dropout','Dropped Out'),('transferred', 'Transferred')],string='Registration Status',default='draft')
    reason = fields.Text('Reason')

    attendance_count = fields.Integer('Attendance Count',compute="compute_attendance")
    avg_attendance = fields.Float('Avg attendance (%)',compute="compute_attendance")
    nb_attendance = fields.Float('Nb of Attended',compute="compute_attendance")
    registration_number = fields.Char('Registration Number')
    reason_if_failed = fields.Text('Reason if failed')
    progress = fields.Float('Progress')
    membership = fields.Boolean('Membership')
    membership_purchase_date = fields.Date('Membership Purchase Date')
    coupon_code_used = fields.Char('Coupon Used Code')
    candidate_id = fields.Char('Candidate ID')
    entrance_fee_date = fields.Date('Entrance Fee Purchase Date')
    company_id = fields.Many2one('res.company',related=False,string='Region')
    mrm_id = fields.Integer('MRM ID')
    from_mrm = fields.Boolean()

    def create_attendance(self):
        if self.state == 'open' and self.transfer_status == 'active':
            if self.event_id and not self.session_id:
                for session in self.event_id.track_ids:
                    attendance = self.env['attendance'].sudo().search([('registration_id','=',self.id),('session_id','=',session.id),('event_id','=',self.event_id.id),('partner_id','=',self.partner_id.id)])
                    if not attendance:
                        attendance = self.env['attendance'].sudo().create({
                            'registration_id': self.id,
                            'event_id': self.event_id.id,
                            'session_id': session.id,
                            'partner_id': self.partner_id.id
                            })

            elif self.session_id:
                attendance = self.env['attendance'].sudo().search([('registration_id','=',self.id),('session_id','=',self.session_id.id),('partner_id','=',self.partner_id.id)])
                if not attendance:
                    attendance = self.env['attendance'].sudo().create({
                        'registration_id': self.id,
                        'session_id': self.session_id.id,
                        'partner_id': self.partner_id.id,
                        'event_id': self.session_id.event_id.id,
                        })


        elif self.state == 'cancel' or self.transfer_status in ['dropout','transferred']:
            today = fields.Datetime.now()
            attendances = self.env['attendance'].search([('registration_id','=',self.id),('session_id.date','>',today)]).sudo().unlink()

    """def write(self, vals):
        res = super(EventRegistration, self).write(vals)

        if self.state == 'open' and self.transfer_status == 'active':
            if self.event_id and not self.session_id:
                for session in self.event_id.track_ids:
                    attendance = self.env['attendance'].search([('registration_id','=',self.id),('session_id','=',session.id),('event_id','=',self.event_id.id),('partner_id','=',self.partner_id.id)])
                    if not attendance:
                        attendance = self.env['attendance'].create({
                            'registration_id': self.id,
                            'event_id': self.event_id.id,
                            'session_id': session.id,
                            'partner_id': self.partner_id.id
                            })

            elif self.session_id:
                attendance = self.env['attendance'].search([('registration_id','=',self.id),('session_id','=',self.session_id.id),('partner_id','=',self.partner_id.id)])
                if not attendance:
                    attendance = self.env['attendance'].create({
                        'registration_id': self.id,
                        'session_id': self.session_id.id,
                        'partner_id': self.partner_id.id,
                        'event_id': self.session_id.event_id.id,
                        })


        elif self.state == 'cancel' or self.transfer_status in ['dropout','transferred']:
            today = fields.Datetime.now()
            attendances = self.env['attendance'].search([('registration_id','=',self.id),('session_id.date','>',today)]).unlink()


        return res"""

    def compute_attendance(self):
        for record in self:
            record.avg_attendance = 0
            attendances = self.env['attendance'].sudo().search([('registration_id','=',record.id),('registration_id.state','!=','cancel')])
            record.attendance_count = len(attendances)

            attended = self.env['attendance'].sudo().search([('registration_id','=',record.id),('attended','=',1),('registration_id.state','!=','cancel'),('registration_id.transfer_status','=','active'),('session_id.stage_id','=',self.env.ref('website_event_track.event_track_stage1').id)])
            record.nb_attendance = len(attended)

            record.avg_attendance = 0
            if len(attended) > 0:
                record.avg_attendance = (len(attended) * 100) / len(attendances)

    def action_confirm(self):
        res = super(EventRegistration, self).action_confirm()
        self.sudo().write({'transfer_status': 'active'})
        return res 

    """def button_reg_close(self):
        for registration in self:
            today = fields.Datetime.now()
            if registration.event_id.date_begin <= today and registration.event_id.state == 'confirm':
                if registration.event_id and not registration.session_id:
                    for session in self.event_id.track_ids:
                        attendance = self.env['attendance'].search([('registration_id','=',registration.id),('session_id','=',session.id),('event_id','=',registration.event_id.id),('partner_id','=',registration.partner_id.id)])
                        if not attendance:
                            attendance = self.env['attendance'].create({
                                'registration_id': registration.id,
                                'event_id': registration.event_id.id,
                                'session_id': registration.session_id.id if registration.session_id else False,
                                'partner_id': registration.partner_id.id if registration.partner_id else False
                                }) 

                res = {
                'type': 'ir.actions.act_window',
                'name': _('Attendance'),
                'view_mode': 'tree',
                'res_model': 'attendance',
                'domain' : [('id','=',attendance.id)],
                'target': 'current',
                }

                return res

            elif registration.event_id.state == 'draft':
                raise UserError(_("You must wait the event confirmation before doing this action."))

            else:
                raise UserError(_("You must wait the event starting day before doing this action."))"""
                



