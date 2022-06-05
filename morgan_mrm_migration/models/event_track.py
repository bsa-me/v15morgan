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


class EventTrack(models.Model):
    _inherit = 'event.track'
    mrm_id = fields.Integer('MRM ID')
    tfrm_id = fields.Integer('TFRM ID') 


    def migrate_sessions(self):
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

        currentOrder = self.env['ir.config_parameter'].browse(74).value
        events = models.execute_kw(mip_db, uid, mip_password,'event.event', 'search_read',[[['mrm_id', '>', 0]]], {'fields': ['mrm_id'],'offset': int(currentOrder), 'limit': 100})
        if events:
            for event in events:
                event_url = mrm_url + 'events/events?_display=sessions.code,sessions.title,sessions.start,sessions.end,id,type,course,title,code,location,region.name,region.id,personnel,prices,start,end,location_name,compound_children&type__in=multisession,compound,normal&id=' + str(event['mrm_id'])
                details_req = requests.get(event_url,auth=(mrm_username, mrm_password))
                valid_json = False
                try:
                    details_response = details_req.json()
                    if details_response:
                        instructor = False
                        if "personnel" in details_response[0]:
                            for personnel in details_response[0]["personnel"]:
                                instructor = models.execute_kw(mip_db, uid, mip_password,'hr.employee', 'search',[[['mrm_id', '=', personnel['id']]]])
                                if not instructor:
                                    employee_vals = {}
                                    employee_vals['mrm_id'] = personnel['id']
                                    if personnel['contact']:
                                        employee_vals['work_email'] = personnel['contact']['email']
                                        employee_vals['name'] = personnel['contact']['name']

                                    employee_vals['is_instructor'] = True

                                    if 'name' in employee_vals:
                                        instructor = models.execute_kw(mip_db, uid, mip_password,
                                            'hr.employee', 'create',[employee_vals])

                                else:
                                    instructor = instructor[0]

                            
                        if "sessions" in details_response[0]:
                            for session in details_response[0]["sessions"]:
                                session_date = session['start']
                                session_start = datetime.strptime (session_date, "%Y-%m-%dT%H:%M:%SZ")
                                session_date = session_start.strftime('%Y-%m-%d')
                                session_from = session_start.strftime('%H:%M')
                                session_from = session_from.replace(":",".")

                                session_end = session['end']
                                session_end = datetime.strptime(session_end, "%Y-%m-%dT%H:%M:%SZ")
                                session_to = session_end.strftime('%H:%M')
                                session_to = session_to.replace(":",".")

                                vals = {}
                                vals['event_id'] = event['id']
                                vals['mrm_id'] = session['id']
                                vals['name'] = session['title']
                                vals['date'] = session_date
                                vals['track_from'] = float(session_from)
                                vals['to'] = float(session_to)
                                vals['employee_id'] = instructor

                                event_track = models.execute_kw(mip_db, uid, mip_password,'event.track', 'search',[[['mrm_id', '=', session['id']]]])
                                if not event_track:
                                    event_track = models.execute_kw(mip_db, uid, mip_password,
                                        'event.track', 'create',[vals])
                                    print(str(event_track))
                                else:
                                    print("event track exist")

                except:
                    print(event['mrm_id'])


                    

        currentOrder = int(currentOrder) + 100
        models.execute_kw(mip_db, uid, mip_password, 'ir.config_parameter', 'write', [[74], {
            'value': str(currentOrder)
            }])
