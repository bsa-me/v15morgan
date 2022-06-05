import json
import requests
import xmlrpc.client as xmlrpclib
import base64
from datetime import timedelta,datetime
from odoo import models, fields
from odoo.exceptions import UserError


class Course(models.Model):
    _inherit = 'course'
    mrm_id = fields.Integer('MRM ID')
    tfrm_id = fields.Integer('TFRM ID')

    def migrate_courses(self):
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

        currentOrder = self.env['ir.config_parameter'].browse(71).value
        hasData = True

        while(hasData):
            response = requests.get(mrm_url + 'event/courses?id__gt=' + str(currentOrder) + '&_order=id&_limit=100',
                auth=(mrm_username, mrm_password))

            records = response.json()
            if(not records):
                hasData = False

            for rec in records:
                vals = {}
                rec_id = rec['id']
                print ('Loading course: ' + str(rec_id))
                details_req = requests.get(
                    mrm_url + 'event/courses/' + str(rec_id),
                    auth=(mrm_username, mrm_password))

                details_response = details_req.json()
                vals['mrm_id'] = rec_id
                vals['name'] = rec['title']

                program = models.execute_kw(mip_db, uid, mip_password,'program', 'search',[[['name', '=', details_response["categories"][0]["name"]]]])
                if not program:
                    program_vals = {}
                    program_vals['name'] = details_response["categories"][0]["name"]
                    program_vals['mrm_id'] = details_response["categories"][0]["id"]
                    program = models.execute_kw(mip_db, uid, mip_password,
                        'program', 'create',[program_vals])
                else:
                    program = program[0]

                vals['program_id'] = program
                #vals['active'] = True if rec['is_archived'] == False else False
                vals['subject_area'] = rec['introduction']



                course = models.execute_kw(mip_db, uid, mip_password,'course', 'search',[[['mrm_id', '=', rec_id]]])
                if not course:
                    odoo_rec = models.execute_kw(mip_db, uid, mip_password,
                        'course', 'create',[vals])
                    print(str(odoo_rec))

                else:
                    print("course exist")

            currentOrder = int(currentOrder) + 100
            models.execute_kw(mip_db, uid, mip_password, 'ir.config_parameter', 'write', [[71], {
                'value': str(currentOrder)
                }])

    def migrate_course_pricing(self):
        companies = {}
        mrm_url = 'https://mrm.morganintl.com/api/v2/'
        mrm_username = 'itx@morganintl.com'
        mrm_password = 'Morgan#2018'
        mip_url = 'http://staging.morganintl.com'
        mip_db = 'morgan13-stage-1493458'
        mip_username = 'no-reply@morganintl.com'
        mip_password = 'admin'

        companies["AUH"] = 21
        companies["ACI"] = 63
        companies["AAD"] = 31
        companies["UCB"] = 16
        companies["DOH"] = 87
        companies["ALQ"] = 88
        companies["ALX"] = 89
        companies["AUT"] = 18
        companies["ADJ"] = 90
        companies["AUS"] = 91
        companies["UOB"] = 92
        companies["BGL"] = 93
        companies["ABG"] = 2
        companies["BNGKey"] = 155
        companies["BAL"] = 94
        companies["BAN"] = 95
        companies["ROF"] = 55
        companies["BAU"] = 96
        companies["BRU"] = 97
        companies["CGT"] = 98
        companies["AUC"] = 99
        companies["CAL"] = 100
        companies["CHD"] = 101
        companies["CHG"] = 102
        companies["CHN"] = 28
        companies["CHR"] = 103
        companies["CHL"] = 104
        companies["CHE"] = 105
        companies["COC"] = 32
        companies["COL"] = 108
        companies["COH"] = 109
        companies["CSL"] = 110
        companies["COR"] = 111
        companies["DMS"] = 112
        companies["TAD"] = 36
        companies["DXB"] = 15
        companies["EGY"] = 113
        companies["LUX"] = 114
        companies["GNV"] = 115
        companies["HDB"] = 29
        companies["HRB"] = 116
        companies["HDT"] = 117
        companies["TRI"] = 73
        companies["HYL"] = 118
        companies["IND"] = 119
        companies["QAR"] = 120
        companies["INTL"] = 121
        companies["BHR"] = 122
        companies["JAI"] = 123
        companies["TAJ"] = 37
        companies["JNI"] = 20
        companies["JUB"] = 124
        companies["KAR"] = 125
        companies["KLK"] = 126
        companies["KOL"] = 127
        companies["KWT"] = 128
        companies["KWO"] = 129
        companies["LAC"] = 130
        companies["BHM"] = 131
        companies["BIBF"] = 132
        companies["BHD"] = 133
        companies["MAN"] = 11
        companies["MAR"] = 134
        companies["MOR"] = 135
        companies["MUB"] = 136
        companies["MUM"] = 137
        companies["OMR"] = 138
        companies["SHAH"] = 139
        companies["DLH"] = 27
        companies["NDEL"] = 140
        companies["DEL"] = 141
        companies["OL"] = 142
        companies["OTH"] = 143
        companies["OTW"] = 144
        companies["PKS"] = 145
        companies["PAR"] = 146
        companies["PUN"] = 26
        companies["PHO"] = 147
        companies["PNQ"] = 148
        companies["QFC"] = 149
        companies["QBC"] = 7
        companies["TAR"] = 35
        companies["SAS"] = 150
        companies["TER"] = 13
        companies["TOR"] = 151
        companies["USK"] = 152
        companies["VCR"] = 153
        companies["ZUR"] = 154


        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(mip_url),allow_none=True)
        common.version()
        uid = common.authenticate(mip_db, mip_username, mip_password, {})
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(mip_url),allow_none=True)

        currentOrder = self.env['ir.config_parameter'].browse(71).value
        courses = models.execute_kw(mip_db, uid, mip_password,'course', 'search_read',[[['mrm_id', '>', 0]]], {'fields': ['mrm_id']})
        if courses:
            for course in courses:
                details_req = requests.get(
                    mrm_url + 'event/courses/' + str(course['mrm_id']),
                    auth=(mrm_username, mrm_password))

                details_response = details_req.json()
                #raise UserError(str(details_response["mapped_items"][0]["pricing"][0]["region"]["company"]))
                for pricing in details_response["mapped_items"]:
                    raise UserError(str(pricing['pricing']))
                    company = models.execute_kw(mip_db, uid, mip_password,'course', 'search_read',[[['mrm_id', '>', 0]]], {'fields': ['mrm_id']})

        currentOrder = int(currentOrder) + 100
        models.execute_kw(mip_db, uid, mip_password, 'ir.config_parameter', 'write', [[71], {
            'value': str(currentOrder)
            }])
