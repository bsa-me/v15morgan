import base64
from datetime import timedelta,datetime
from odoo import models, fields, api
from odoo.exceptions import UserError
import xlrd
import string
from zipfile import ZipFile
from openpyxl import load_workbook
import dateparser
from dateutil.parser import parse


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    def fix_user_permissions(self):
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            companies = []
            groups = []
            lines = row.split(',')
            user_email = lines[2].strip()
            user = self.env['res.users'].sudo().search([('login','=',user_email)])
            if lines[3]:
                group_name = lines[3].strip()

                group = self.env['res.groups'].sudo().search([('name','=',group_name)])
                if not group:
                    group = self.env['res.groups'].sudo().search([('name','ilike',group_name)])

                if group:
                    groups.append(group.id)

            if lines[4]:
                company_name = lines[4].strip()
                if company_name == 'All':
                    for company in self.env['res.company'].sudo().search([]):
                        companies.append(company.id)

                elif "/" not in company_name:
                    company = self.env['res.company'].sudo().search([('name','=',company_name)])
                    if not company:
                        company = self.env['res.company'].sudo().search([('name','ilike',company_name)],limit=1,order="id")

                    if company:
                        companies.append(company.id)

                else:
                    names = company_name.split('/')
                    for name in names:
                        company = self.env['res.company'].sudo().search([('name','=',name)])
                        if not company:
                            company = self.env['res.company'].sudo().search([('name','ilike',name)],limit=1,order="id desc")

                        if company:
                            companies.append(company.id)

            if len(companies) > 0:
                user.sudo().write({"company_id": companies[0],"company_ids": [(6, 0, companies)]})

            if len(groups) > 0:
                user_groups = user.groups_id.ids
                groups = groups + user_groups
                user.sudo().write({"groups_id": [(6, 0, groups)]})


