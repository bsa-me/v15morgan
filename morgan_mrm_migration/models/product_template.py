import json
import requests
import xmlrpc.client as xmlrpclib
import base64
from datetime import timedelta,datetime
from odoo import models,fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    tfrm_id = fields.Integer()

    def migrate_products(self):
        mrm_url = 'https://mrm.morganintl.com/api/v2/'
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

        currentOrder = self.env['ir.config_parameter'].browse(67).value
        hasData = True

        while(hasData):
            response = requests.get(mrm_url + 'stock/items?id__gt=' + str(currentOrder) + '&_order=id&_limit=100',
                auth=(mrm_username, mrm_password))

            records = response.json()
            if(not records):
                hasData = False

            for rec in records:
                vals = {}
                rec_id = rec['id']
                print ('Loading product: ' + str(rec_id))
                details_req = requests.get(
                    mrm_url + 'stock/items/' + str(rec_id),
                    auth=(mrm_username, mrm_password))

                details_response = details_req.json()
                if "id" in details_response["categories"]:
                    category = models.execute_kw(mip_db, uid, mip_password,'product.category', 'search',[[['name', '=', details_response["categories"]["name"]]]])
                    if not category:
                        categ_vals = {}
                        categ_vals['name'] = details_response["categories"]["name"]
                        categ_vals['mrm_id'] = details_response["categories"]["id"]
                        category = models.execute_kw(mip_db, uid, mip_password,
                            'product.category', 'create',[categ_vals])

                    else:
                        category = category.id

                    vals['categ_id'] = category

                vals['mrm_id'] = rec_id
                vals['name'] = details_response['name']
                vals['description_sale'] = details_response['description']
                vals['type'] = 'service' if details_response['is_stock'] == False else 'product'
                product = models.execute_kw(mip_db, uid, mip_password,'product.template', 'search',[[['mrm_id', '=', rec_id]]])
                if not product:
                    odoo_rec = models.execute_kw(mip_db, uid, mip_password,
                        'product.template', 'create',[vals])
                    print(str(odoo_rec))

                else:
                    print("product exist")

            currentOrder = int(currentOrder) + 100
            models.execute_kw(mip_db, uid, mip_password, 'ir.config_parameter', 'write', [[67], {
                'value': str(currentOrder)
                }])
