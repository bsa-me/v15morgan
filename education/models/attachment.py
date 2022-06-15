from odoo import models, fields
import base64
from odoo.exceptions import UserError


class ProgramAttachment(models.Model):
    _name = 'program.attachment'
    company_id = fields.Many2one('res.company', string="Region", domain="[('is_region', '=', True)]")
    program_id = fields.Many2one('program')
    folder_id = fields.Many2one('documents.folder', string='Folder', store=True)
    document_ids = fields.One2many('documents.document', 'program_attachment_id')
    enrollment = fields.Text('Enrollment')

    def assign_companies_countries(self):
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        for row in reader:
            lines = row.split('\t')

            company = self.env.ref(str(lines[0]))
            if lines[1]:
                country_id = self.env['res.country'].search([('name', '=', str(lines[1]))])
                if country_id:
                    if len(country_id) > 0:
                        raise UserError("Multiple results for country " + str(lines[1]))
                else:
                    raise UserError(lines[1] + " this country does not exist")
            if company:
                company.write({
                    'country_id': country_id.id,
                })
            else:
                raise UserError("Company of ref " + str(lines[0]) + " does not exist")
