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


class Employee(models.Model):
    _inherit = 'hr.employee'
    mrm_id = fields.Integer('MRM ID')
    mrm_status = fields.Char()
    tfrm_id = fields.Integer('TFRM ID')

class PublicEmployee(models.Model):
    _inherit = 'hr.employee.public'
    mrm_id = fields.Integer('MRM ID')
    mrm_status = fields.Char()
    tfrm_id = fields.Integer('TFRM ID')
