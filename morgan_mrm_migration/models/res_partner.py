import json
import requests
import xmlrpc.client as xmlrpclib
import base64
from datetime import timedelta,datetime
from odoo import models,fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    from_excel = fields.Boolean()
    tfrm_id = fields.Integer()
    is_mrm_contact = fields.Boolean()
    job_role = fields.Char()
    registration_ids = fields.One2many('event.registration','partner_id',string='Registrations')

    def migrate_accounts(self):
        mrm_url = 'https://mrm.morganintl.com/beta/api/'
        mrm_username = 'itx@morganintl.com'
        mrm_password = 'Morgan#2018'

        mip_url = 'http://staging.morganintl.com'
        mip_db = 'morgan13-stage-1493458'
        mip_username = 'no-reply@morganintl.com'
        mip_password = 'admin'

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(mip_url),allow_none=True)
        common.version()
        uid = common.authenticate(mip_db, mip_username, mip_password, {})
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(mip_url),allow_none=True)

        currentOrder = self.env['ir.config_parameter'].browse(65).value
        hasData = True

        while(hasData):
            response = requests.get(mrm_url + 'crm/accounts?id__gt=' + str(currentOrder) + '&_order=id&_limit=100',
                auth=(mrm_username, mrm_password))

            records = response.json()
            if(not records):
                hasData = False

            for rec in records:
                vals = {}
                rec_id = rec['id']
                print ('Loading Account: ' + str(rec_id))
                details_req = requests.get(
                    mrm_url + 'crm/accounts/' + str(rec_id),
                    auth=(mrm_username, mrm_password))

                details_response = details_req.json()
                country = False
                if "address_country" in details_response:
                    if details_response["address_country"]:
                        code = details_response["address_country"]["id"]
                        country = models.execute_kw(mip_db, uid, mip_password,'res.country', 'search',[[['code', '=', code]]])

                vals['mrm_id'] = details_response['id']
                vals['name'] = details_response['name']
                vals['phone'] = details_response['telephone']
                vals['vat'] = details_response['vat_number']
                vals['country_id'] = country[0] if country else False
                vals['street'] = details_response['address_street']
                vals['zip'] = details_response['address_postcode']

                if 'email' in details_response:
                    if details_response['email']:
                        vals['email'] = details_response['email'] if len(details_response['email']) > 0 else False

                else:
                    vals['email'] = False

                vals['website'] = details_response['website']
                vals['mobile'] = details_response['mobile']
                vals['company_type'] = 'company' if details_response['is_individual'] == False else 'person'
                vals['account_type'] = 'b2b' if details_response['is_individual'] == False else 'b2c'
                vals['fax'] = details_response['fax']
                vals['mrm_bank_details'] = details_response['bank_details']
                vals['parent_mrm_id'] = details_response['parent_id']

                if 'email' in details_response:
                    if details_response['email']:
                        if len(details_response['email']) > 0:
                            contact = models.execute_kw(mip_db, uid, mip_password,'res.partner', 'search',[[['mrm_id', '=', details_response['id']]]])
                            if not contact:
                                odoo_rec = models.execute_kw(mip_db, uid, mip_password,
                                    'res.partner', 'create',[vals])

                                print(str(odoo_rec))

                            else:
                                print("Contact exit " + str(contact[0]))

                        else:
                            odoo_rec = models.execute_kw(mip_db, uid, mip_password,
                                'res.partner', 'create',[vals])
                            print(str(odoo_rec))
                    else:
                        vals['email'] = False
                        odoo_rec = models.execute_kw(mip_db, uid, mip_password,
                            'res.partner', 'create',[vals])


                else:
                    odoo_rec = models.execute_kw(mip_db, uid, mip_password,
                        'res.partner', 'create',[vals])
                    print(str(odoo_rec))
            currentOrder = int(currentOrder) + 100
            models.execute_kw(mip_db, uid, mip_password, 'ir.config_parameter', 'write', [[65], {
                'value': str(currentOrder)
                }])
