from odoo import models, fields , api, _


class Program(models.Model):
    _name = 'program'
    _description = 'Program'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'format.address.mixin']
    name = fields.Char(string='Program', translate=True)
    course_ids = fields.One2many('course', 'program_id', string='Courses')
    description = fields.Char('Description')
    enrollment = fields.Text('Enrollment Agreement')
    company_id = fields.Many2one('res.company', string="Region")
    folder_id = fields.Many2one('documents.folder', string="Workspace")
    program_attachment_ids = fields.One2many('program.attachment', 'program_id', string="Program Attachments")
    courses_count = fields.Integer(string="Courses", compute="_compute_count_courses", readonly=True)
    mrm_id = fields.Integer('MRM ID')
    active = fields.Boolean(default=True)
    
    def action_view_courses(self):
      return {
            "name": _("Courses"),
            "type": 'ir.actions.act_window',
            "res_model": 'course',
            "view_mode": "tree,form",
            "domain": [('program_id', '=', self.id)]
        }

    def _compute_count_courses(self):
        for record in self:
            contracts = self.env['course'].search([('program_id', '=', self.id)])
            record['courses_count'] = len(contracts)
            
    @api.model
    def create(self, vals):
      record = super(Program, self).create(vals)
      folder = self.env['documents.folder'].create({
        'name': record['name'],
        'parent_folder_id': self.env.ref('education.workspace_program_attachment').id
      })
      record['folder_id'] = folder.id
      return record

    def write(self, vals):
      record = super(Program, self).write(vals)
      if(self.folder_id):
        self.folder_id.write({'name': self.name})
      else:
        new_folder_id = self.env['documents.folder'].create(
          {
            'name': self.name,
            'parent_folder_id':self.env.ref('education.workspace_program_attachment').id
          })
        vals['folder_id'] = new_folder_id.id
        return super(Program, self).write(vals)

