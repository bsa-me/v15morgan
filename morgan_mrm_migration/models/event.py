import json
import requests
import xmlrpc.client as xmlrpclib
import base64
from datetime import timedelta,datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

regions = {}
regions["AUH"] = 21
regions["ACI"] = 63
regions["AAD"] = 31
regions["UCB"] = 16
regions["DOH"] = 87
regions["ALQ"] = 88
regions["ALX"] = 89
regions["AUT"] = 18
regions["ADJ"] = 90
regions["AUS"] = 91
regions["UOB"] = 92
regions["BGL"] = 93
regions["ABG"] = 2
regions["BNGKey"] = 155
regions["BAL"] = 94
regions["BAN"] = 95
regions["ROF"] = 55
regions["BAU"] = 96
regions["BRU"] = 97
regions["CGT"] = 98
regions["AUC"] = 99
regions["CAL"] = 100
regions["CHD"] = 101
regions["CHG"] = 102
regions["CHN"] = 28
regions["CHR"] = 103
regions["CHL"] = 104
regions["CHE"] = 105
regions["COC"] = 32
regions["COL"] = 108
regions["COH"] = 109
regions["CSL"] = 110
regions["COR"] = 111
regions["DMS"] = 112
regions["TAD"] = 36
regions["DXB"] = 15
regions["EGY"] = 113
regions["LUX"] = 114
regions["GNV"] = 115
regions["HDB"] = 29
regions["HRB"] = 116
regions["HDT"] = 117
regions["TRI"] = 73
regions["HYL"] = 118
regions["IND"] = 119
regions["QAR"] = 120
regions["INTL"] = 121
regions["BHR"] = 122
regions["JAI"] = 123
regions["TAJ"] = 37
regions["JNI"] = 20
regions["JUB"] = 124
regions["KAR"] = 125
regions["KLK"] = 126
regions["KOL"] = 127
regions["KWT"] = 128
regions["KWO"] = 129
regions["LAC"] = 130
regions["BHM"] = 131
regions["BIBF"] = 132
regions["BHD"] = 133
regions["MAN"] = 11
regions["MAR"] = 134
regions["MOR"] = 135
regions["MUB"] = 136
regions["MUM"] = 137
regions["OMR"] = 138
regions["SHAH"] = 139
regions["DLH"] = 27
regions["NDEL"] = 140
regions["DEL"] = 141
regions["OL"] = 142
regions["OTH"] = 143
regions["OTW"] = 144
regions["PKS"] = 145
regions["PAR"] = 146
regions["PUN"] = 26
regions["PHO"] = 147
regions["PNQ"] = 148
regions["QFC"] = 149
regions["QBC"] = 7
regions["TAR"] = 35
regions["SAS"] = 150
regions["TER"] = 13
regions["TOR"] = 151
regions["USK"] = 152
regions["VCR"] = 153
regions["ZUR"] = 154


class Event(models.Model):
    _inherit = 'event.event'
    mrm_id = fields.Integer('MRM ID')
    created_at = fields.Datetime('MRM Created At')
    tfrm_id = fields.Integer('TFRM ID')

    @api.constrains('date_begin', 'date_end')
    def _check_closing_date(self):
        for event in self:
            try:
                if event.date_end < event.date_begin:
                    return

            except:
                return

    def migrate_events(self):
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

        currentOrder = self.env['ir.config_parameter'].browse(72).value
        hasData = True

        while(hasData):
            response = requests.get(mrm_url + 'event/public_events?id__gt=' + str(currentOrder) + '&_order=id&_limit=20',
                auth=(mrm_username, mrm_password))

            try:
                records = response.json()
                if(not records):
                    hasData = False


                for rec in records:
                    vals = {}
                    rec_id = rec['id']
                    print ('Loading event: ' + str(rec_id))
                    details_req = requests.get(
                        mrm_url + 'event/public_events/' + str(rec_id),
                        auth=(mrm_username, mrm_password))

                    details_response = details_req.json()
                    date_begin = False

                    date_begin = details_response['start_date']
                    if date_begin:
                        date_begin = datetime.strptime (date_begin, "%Y-%m-%dT%H:%M:%S")
                        date_begin = date_begin.strftime('%Y-%m-%d %H:%M:%S')

                    date_end = details_response['end_date']
                    date_end = datetime.strptime (date_end, "%Y-%m-%dT%H:%M:%S")
                    date_end = date_end.strftime('%Y-%m-%d %H:%M:%S')

                    if not date_begin and date_end:
                        date_begin = date_end

                    vals['date_begin'] = date_begin
                    vals['date_end'] = date_end
                    vals['mrm_id'] = rec_id
                    vals['name'] = rec['title']
                    vals['is_online'] = rec['is_online']

                    program = models.execute_kw(mip_db, uid, mip_password,'program', 'search',[[['name', '=', details_response["course"]["categories"][0]["name"]]]])
                    if not program:
                        program_vals = {}
                        program_vals['name'] = details_response["course"]["categories"][0]["name"]
                        program_vals['mrm_id'] = details_response["course"]["categories"][0]["id"]
                        program = models.execute_kw(mip_db, uid, mip_password,
                            'program', 'create',[program_vals])

                    else:
                        program = program[0]

                    vals['program_id'] = program


                    #company_id = models.execute_kw(mip_db, uid, mip_password,'res.company', 'search',[[['mrm_id', '=', details_response["company_id"]]]])[0]
                    #vals['company_id'] = company_id

                    term_id = models.execute_kw(mip_db, uid, mip_password,'term', 'search',[[['mrm_id', '=', details_response["tag_id"]]]])[0]
                    vals['term_id'] = term_id

                    course_id = models.execute_kw(mip_db, uid, mip_password,'course', 'search',[[['mrm_id', '=', details_response["course_id"]]]])
                    if course_id:
                        vals['course_id'] = course_id[0]

                    vals['company_id'] = regions.get(details_response["region_id"])


                    event = models.execute_kw(mip_db, uid, mip_password,'event.event', 'search',[[['mrm_id', '=', rec_id]]])
                    if not event:
                        event = models.execute_kw(mip_db, uid, mip_password,
                            'event.event', 'create',[vals])
                        print(str(event))

                    else:
                        event = event[0]
                        print("event exist")

            except:
                print("error")





            currentOrder = int(currentOrder) + 20
            models.execute_kw(mip_db, uid, mip_password, 'ir.config_parameter', 'write', [[72], {
                'value': str(currentOrder)
                }])

    def import_events(self):

        currencies = {
        'Bahraini Dinar': self.env.ref('base.BHD').id,
        'Canadian Dollars ': self.env.ref('base.CAD').id,
        'Indian Rupee': self.env.ref('base.INR').id,
        'Jordanian Dinar': self.env.ref('base.JOD').id,
        'Lebanese Pound': self.env.ref('base.LBP').id,
        'Saudi Riyal': self.env.ref('base.SAR').id,
        'U.S. Dollars': self.env.ref('base.USD').id,
        'United Arab Emirates Dirham': self.env.ref('base.AED').id,
        }

        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            lines = row.split('\t')
            vals = {}
            vals['mrm_id'] = lines[0]
            
            term = self.env['term'].search([('name','=',lines[1])])
            if not term:
                term = self.env['term'].create({
                    'name': lines[1]
                    })


            vals['term_id'] = term.id
            
            
            program = self.env['program'].search([('mrm_id','=',int(lines[3]))],limit=1)
            if not program:
                program = self.env['program'].create({
                    'name': lines[2],
                    'mrm_id': int(lines[3]),
                    })

            vals['program_id'] = program.id

            vals['course_id'] = self.env['course'].search([('mrm_id','=', int(lines[5]))])
            vals['date_begin'] = datetime.strptime (lines[6], "%Y-%m-%d %H:%M:%S")
            vals['date_end'] = datetime.strptime (lines[7], "%Y-%m-%d %H:%M:%S")
            vals['company_id'] = self.env['res.company'].search([('name','=',lines[10])],limit=1).id

            status = False
            if lines[17] == True:
                status = 'draft'

            if lines[18] == True:
                vals['is_online'] = True
                raise UserError('test')

            if lines[19] == True:
                status = 'cancel'

            vals['state'] = status

            event = self.search([('mrm_id','=',vals['mrm_id'])],limit=1)
            if not event:
                event = self.create(vals)

            else:
                event.write(vals)

            ticket_vals = {}
            ticket_vals['event_id'] = event.id
            ticket_vals['name'] = 'Tuition fees'
            ticket_vals['ticket_company_id'] = event.company_id.id
            ticket_vals['price'] = float(lines[21])

            ticket = self.env['event.event.ticket'].search([('name','=','Tuition fees'),('event_id','=',event.id)])
            if not ticket:
                ticket = self.env['event.event.ticket'].create(vals)

            else:
                ticket.write(vals)


    def import_prices(self, mrm_id):
        mrm_url = 'https://mrm.morganintl.com/api/v2/'
        mrm_username = 'itx@morganintl.com'
        mrm_password = 'Morgan#2018'

        details_req = requests.get(
            mrm_url + 'event/event_prices?event_id=' + str(mrm_id),
            auth=(mrm_username, mrm_password))

        try:
            details_response = details_req.json()
            for resp in details_response:
                vals = {}
                vals['price'] = resp["price"]
                vals['mrm_currency'] = self.env['res.currency'].search([('name','=',resp["currency"]["code"])]).id
                vals['event_id'] = self.env['event.event'].search([('mrm_id','=',mrm_id)]).id
                vals['ticket_company_id'] = self.env['event.event'].search([('mrm_id','=',mrm_id)]).company_id.id
                vals['name'] = resp["price_level"]["name"]
                vals['mrm_id'] = resp["id"]

                ticket = self.env['event.event.ticket'].search([('mrm_id','=',resp["id"])])
                if not ticket:
                    ticket = self.env['event.event.ticket'].create(vals)

                else:
                    ticket.write(vals)

        except:
            print('error')


    def import_europe_prices(self, mrm_id):
        mrm_url = 'https://tfrm.administrateapp.com/api/v2/'
        mrm_username = 'itx@morganintl.com'
        mrm_password = 'itx@morganintl.com'

        details_req = requests.get(
            mrm_url + 'event/event_prices?event_id=' + str(mrm_id),
            auth=(mrm_username, mrm_password))

        details_response = details_req.json()
        for resp in details_response:
            vals = {}
            vals['price'] = resp["price"]
            vals['mrm_currency'] = self.env['res.currency'].search([('name','=',resp["currency"]["code"])]).id
            vals['event_id'] = self.env['event.event'].search([('mrm_id','=',mrm_id)]).id
            vals['ticket_company_id'] = self.env['event.event'].search([('mrm_id','=',mrm_id)]).company_id.id
            vals['name'] = resp["price_level"]["name"]
            vals['mrm_id'] = resp["id"]

            ticket = self.env['event.event.ticket'].search([('mrm_id','=',resp["id"])])
            if not ticket:
                ticket = self.env['event.event.ticket'].create(vals)

            else:
                ticket.write(vals)





    def add_prices_to_course(self):
        date = datetime.now().strftime('%Y-%m-%d')
        if self.event_ticket_ids:
            for ticket in self.event_ticket_ids:
                region_price = self.env['company.price'].search([('course_region_id','=',self.course_id.id),('company_id','=',ticket.ticket_company_id.id)],limit=1)
                if not region_price:
                    region_price = self.env['company.price'].create({
                        'company_id': ticket.ticket_company_id.id,
                        'course_region_id': self.course_id.id,
                        'tax_ids': ticket.tax_ids.ids,
                        })

                else:
                    region_price.write({
                        'company_id': ticket.ticket_company_id.id,
                        'course_region_id': self.course_id.id,
                        'tax_ids': ticket.tax_ids.ids,
                        })


                region_ticket = self.env['course.ticket.price'].search([('ticket_id','=',region_price.id)])
                if not region_ticket:
                    region_ticket = self.env['course.ticket.price'].create({
                        'name': 'Tuition fees',
                        'price': ticket.ticket_company_id.currency_id._convert(ticket.price,self.env.ref('base.USD'),ticket.ticket_company_id,date),
                        'ticket_id': region_price.id,
                        'company_id': region_price.company_id.id,
                        })

                region_ticket._compute_local_price()



