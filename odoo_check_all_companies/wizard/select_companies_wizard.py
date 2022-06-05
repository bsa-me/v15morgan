# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _


class SelectCompanies(models.TransientModel):
    _name = "select.companies.wizard"
    allowed_companies = fields.Many2many('res.company', 'select_company_allowed_rel', 'select_id', 'company_id',string='Allowed Companies')
    company_ids = fields.Many2many('res.company','select_company__rel', 'select_id', 'company_id', string='Companies')


    @api.model
    def default_get(self, fields):
        result = super(SelectCompanies, self).default_get(fields)
        allowed_companies = self.env.user.company_ids.ids
        result['allowed_companies'] = [(6, 0, allowed_companies)]
        result['company_ids'] = [(6, 0, allowed_companies)]
        return result


    def open_companies_url(self):
        if self.company_ids:
            url_host = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            selected_companies = self.company_ids.ids
            companies = str(selected_companies).replace('[',"")
            companies = str(companies).replace(']',"")
            companies = str(companies).replace(' ',"")
            url = url_host + '/web#cids=' + str(companies)
            #raise Warning(url)
            return {
            'name': 'Companies',
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': url
            }

