from odoo import models, fields

class ProgramAttachment(models.Model):
    _name = 'program.attachment'
    company_id = fields.Many2one('res.company',string="Region", domain="[('is_region', '=', True)]")
    program_id = fields.Many2one('program')
    folder_id = fields.Many2one('documents.folder',string='Folder',store=True)
    document_ids = fields.One2many('documents.document','program_attachment_id')
    enrollment = fields.Text('Enrollment')