from odoo import models, fields, api

class Document(models.Model):
    _inherit = 'documents.document'
    partner_id = fields.Many2one('res.partner', string='Partner')
    program_attachment_id = fields.Many2one('program.attachment')
    company_id = fields.Many2one('res.company',string="Region")
    employee_id = fields.Many2one('hr.employee',string='Instructor',domain="[('is_instructor','=',True)]")
    #attachment_id = fields.Many2one('program.attachment')


    @api.model
    def create(self, vals):
    	record = super(Document, self).create(vals)
    	folder = record.folder_id
    	if 'folder_id' in vals:
    		folder = self.env['documents.folder'].browse(vals['folder_id'])

    	employee = self.env['hr.employee'].search([('folder_id','=',folder.id)],limit=1)
    	if employee:
    		record['employee_id'] = employee.id

    	return record

    def write(self, vals):
    	folder = self.folder_id
    	if 'folder_id' in vals:
    		folder = self.env['documents.folder'].browse(vals['folder_id'])

    	employee = self.env['hr.employee'].search([('folder_id','=',folder.id)],limit=1)
    	if employee:
    		vals['employee_id'] = employee.id

    	return super(Document, self).write(vals)
   

