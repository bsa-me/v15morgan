# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from bs4 import BeautifulSoup
import xlwt
import base64


class ExportViews(models.Model):
	_name = 'odoo.export.view'
	view_id = fields.Many2one('ir.ui.view',required=True)
	model = fields.Char(related="view_id.model",string='Model')


	def parse_xml_to_excel(self):
		arch_base = self.view_id.arch_base
		inherit_views = self.view_id.inherit_children_ids
		for view in inherit_views:
			arch_base += view.arch_base

		model_desc = self.env['ir.model'].search([('model','=',self.model)]).name

		parsed_xml = BeautifulSoup(arch_base)

		buttons = parsed_xml.findAll("button")
		#raise UserError(buttons)
		button_strings = []

		for i in range(0,len(buttons) - 1):
			button_strings.append(buttons[i].get("string"))

		fields = parsed_xml.findAll("field")
		field_names = []

		for i in range(0,len(fields) - 1):
			field_names.append(fields[i]["name"])

		workbook = xlwt.Workbook()
		worksheet = workbook.add_sheet(model_desc)

		xlwt.add_palette_colour("dark_header", 0x21)
		workbook.set_colour_RGB(0x21, 192,27, 27)

		header_title = xlwt.easyxf( "font: colour white, bold on; pattern: pattern solid, fore_colour dark_header;align:horizontal left, indent 1,vertical center" )
		header_title1 = xlwt.easyxf( "font: colour red, bold on;" )

		worksheet.write( 0, 0, 'View Details',header_title)
		worksheet.col( 0 ).width = 8000

		row_index =1
		for line in button_strings:
			if line:
				line = line + ' (button)'
			worksheet.write( row_index, 0, line or '')

			row_index += 1

		
		for line in field_names:
			field_label = self.env['ir.model.fields'].search([('name','=',line)],limit=1).field_description
			worksheet.write( row_index, 0, field_label or '')

			row_index += 1


		if model_desc == 'Lead/Opportunity':
			model_desc = 'Lead-Opportunity'
		filename = model_desc + '.xls'
		workbook.save(filename)

		fp = open(filename, "rb+")
		data = fp.read()
		data64 = base64.encodestring(data)
		
		attach_vals = {
		'name':filename,
		'datas':data64,
		'store_fname':filename,
		}

		doc_id = self.env['ir.attachment'].create(attach_vals)

		return {
		'name':'Excel',
		'res_model':'ir.actions.act_url',
		'type':'ir.actions.act_url',
		'target':'new',
		'url': '/web/content/' + str(doc_id.id) + '?download=true',
		}







