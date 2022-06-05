# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from dateutil import parser
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
import base64
from operator import attrgetter
from io import StringIO
from dateutil.relativedelta import relativedelta
import os
import xlrd
import xlwt



class excel(models.Model):
	_inherit = 'purchase.order'




	def export_data(self, records):
		workbook = xlwt.Workbook()
		worksheet = workbook.add_sheet( 'Sheet 1',cell_overwrite_ok=True)
		xlwt.add_palette_colour("dark_header", 0x21)
		
		header_title = xlwt.easyxf( "font: colour white, bold on; pattern: pattern solid, fore_colour dark_header;align:horizontal left, indent 1,vertical center" )
		header_title1 = xlwt.easyxf( "font: colour red, bold on;" )
		row_index = 0
		sumCount = 0
		worksheet.row( row_index ).height = 350
		
		base_style = xlwt.easyxf( 'align: horizontal left,wrap yes,indent 1,vertical center' )
		date_style = xlwt.easyxf( 'align: horizontal left,wrap yes, indent 1,vertical center', num_format_str='YYYY-MM-DD' )
		datetime_style = xlwt.easyxf( 'align: horizontal left,wrap yes,indent 1,vertical center', num_format_str='YYYY-MM-DD HH:mm:SS' )
	
		worksheet.write( 0, 0, 'City')
		worksheet.col( 0 ).width = 8000  # around 220 pixels
		worksheet.write( 0, 1, 'Shipping Address')
		worksheet.col( 1 ).width = 8000  # around 220 pixels
		worksheet.write( 0, 2, 'Billing Address')
		worksheet.col( 2 ).width = 8000  # around 220 pixels

		dicte = {}	

		for record in records :
				# if record.company_id.name not in dicte.keys() :
				if record.company_id.name not in dicte.keys() :
					product_qty={}
					for line in record.order_line :
						if line.product_id.display_name not in product_qty.keys() :

							#product_qty.setdefault(line.product_id.display_name,[record.company_id.name.adress,record.company_id.display_name,line.product_qty])
							product_qty.setdefault(line.product_id.display_name,[record.company_id.name,record.company_id.display_name,line.product_qty,line.product_id.display_name])
						else:
							
							# product_qty.setdefault(line.product_id.display_name,[record.company_id.name.adress,record.company_id.display_name,str(int(product_qty.get(line.product_id.display_name)[0]+line.product_qty))])					
							d1= {line.product_id.display_name: [record.company_id.name,record.company_id.display_name,int(product_qty.get(line.product_id.display_name)[2]+line.product_qty),line.product_id.display_name]}
							product_qty.update(d1)					



						# dicte.setdefault({record.company_id.name, product_qty})
						dicte.setdefault(record.company_id.name+line.product_id.display_name, product_qty)


				else :
					for line in record.order_line:
						if line.product_id.display_name not in dicte.get(record.company_id.name).keys():
							d={}
							d.setdefault(line.product_id.display_name,[record.company_id.name,record.company_id.display_name,line.product_qty,line.product_id.display_name])
							# dicte.setdefault(record.company_id.name, dicte.get(record.company_id.name).setdefault(line.product_id.display_name,[record.company_id.name.adress,record.company_id.display_name,line.product_qty]))
							dicte.setdefault(record.company_id.name+line.product_id.display_name, d)
						else:
							dp={line.product_id.display_name:[record.company_id.name,record.company_id.display_name,int(line.product_qty+dicte.get(record.company_id.name).get(line.product_id.display_name)[2]),line.product_id.display_name]}
							# d=dicte.get(record.company_id.name).get(line.product_id.display_name).setdefault([record.company_id.name.adress,record.company_id.display_name,dicte.setdefault(record.company_id.name,str(int( dicte.get(record.company_id.name).get(line.product_id.display_name)[2]+line.product_qty)))])
							
							d={record.company_id.name+line.product_id.display_name:dp}
							dicte.update(d)

				row_index=1
				i=0

				

				readed =[]
				tots=[]
		print(dicte)

		for dictionary in dicte.values() :
			for line in dictionary.values():
						
						# table = workbook.get_active_sheet()
						



						# line = [region,company,qty,prdctname]


						#shipping adress
						worksheet.write( row_index, 1, str(line[0]))
						#city
						worksheet.write( row_index, 0, str(line[0]))
						#billing adress
						worksheet.write(row_index, 2, str(line[1]))
						#qty
						
						row_index=row_index+1
						try : 
							print(str(workbook.str_index(str(line[3]))))
							d=readed.index(str(line[3]))+3
							print('this is :')
							print(d-3)
							print('this is the product:')

							print(tots[d-3])
							tots[d-3]=line[2]+tots[d-3]

							worksheet.write( row_index-1 ,d , line[2])
							print(tots)

						
						except Exception :
							#prdct name
							readed.append(str(line[3]))
							d=readed.index(str(line[3]))+3
							worksheet.write( 0, d, str(line[3]))

							tots.append(line[2])
							worksheet.write( row_index-1 ,d , str(line[2]))
							# row_index=row_index+1
							print(tots)
							print(Exception)


		worksheet.write( row_index+1,1 , 'Total Order Quantity:', header_title1)
		for tot in tots :
			worksheet.write(row_index+1,3+tots.index(tot) ,str(tot), header_title1)

		

		ams_time = datetime.datetime.now()
		date = ams_time.strftime('%m-%d-%Y %H.%M.%S')
		filename = 'Report'+ '-' + date +'.xls'
		workbook.save(filename)


		fp = open(filename, "rb+")
		data = fp.read()
		data64 = base64.encodestring(data)
		attach_vals = {
						'name':'Purchase.xls',
						'datas':data64,
						'type': 'binary'
						#'datas_fname':'data.xls',
		  }
		
		doc_id = self.env['ir.attachment'].create(attach_vals).id
		
		return doc_id 


		

		



