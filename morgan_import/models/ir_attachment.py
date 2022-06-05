from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import base64
import requests

class irAttachment(models.Model):
    _inherit = 'ir.attachment'

    
    def import_products(self):
        return False

    
    
    def import_products(self):
        formats = {
        'Self Study': 'self',
        'All': 'all',
        'Live': 'live',
        'Live Online': 'liveonline',
        'Live online': 'liveonline',
        'live': 'live',
        }
        offset = self.env['ir.config_parameter'].browse(43)
        date = datetime.now().strftime('%Y-%m-%d')
        value = offset.value
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        new_value = int(value) + 100
        if new_value > len(reader):
            new_value = len(reader)

        for i in range(int(value), new_value):
            lines = reader[i].split('\t')
            if lines[8]:
                price = False
                cost = False
                is_pack = False
                if lines[7] == 'Package':
                    is_pack = True

                
                product_name = lines[0].strip()

                taxes = []
                product = self.env['product.template'].search([('name','=',product_name),('product_type','=',lines[7])],limit=1)
                vendor = False
                product_category = False                

                if lines[6]:
                    product_category = self.env['product.category'].search([('name','=',lines[6])])
                    if not product_category:
                        product_category = self.env['product.category'].create({
                            'name': lines[6]
                            })


                if lines[4]:
                    cost = lines[4]
                    if "," in cost:
                        cost = cost.replace(",","")

                    cost = float(cost)

                if lines[5]:
                    price = lines[5]
                    if "," in price:
                        price = price.replace(",","")

                    if "CAD  " in price:
                        price = price.replace("CAD  ","")

                    price = float(price)

                if not product:
                    product = self.env['product.template'].create({
                        'name': product_name,
                        'standard_price': cost,
                        'lst_price': price,
                        'product_type': lines[7],
                        'categ_id': product_category.id if product_category else self.env.ref('product.product_category_all').id,
                        'description_sale': lines[10],
                        'description': lines[16],
                        'is_pack': is_pack,
                        'sale_ok': 1,
                        'sale_ok': 1,
                        'study_format': formats[lines[8].strip()],
                        })
                    

                if lines[3]:
                    name_translation = self.env['ir.translation'].search([('lang','=','ar_SY'),('name','=','product.template,name'),('res_id','=',product.id),('type','=','model')],limit=1)
                    if not name_translation:
                        name_translation = self.env['ir.translation'].create({
                            'src': product_name,
                            'value': lines[3],
                            'name': 'product.template,name',
                            'lang': 'ar_SY',
                            'type': 'model',
                            'state': 'translated',
                            'res_id': product.id
                            })
                    else:
                        name_translation.write({
                            'value': lines[3],
                            'state': 'translated',
                            })

                if lines[11]:
                    desc_translation = self.env['ir.translation'].search([('lang','=','ar_SY'),('name','=','product.template,description_sale'),('res_id','=',product.id),('type','=','model')],limit=1)
                    if not desc_translation:
                        desc_translation = self.env['ir.translation'].create({
                            'src': lines[10],
                            'value': lines[11],
                            'name': 'product.template,description_sale',
                            'lang': 'ar_SY',
                            'type': 'model',
                            'state': 'translated',
                            'res_id': product.id,
                            })

                    else:
                        desc_translation.write({
                            'value': lines[11],
                            'state': 'translated'
                            })

                if lines[1]:
                    product.write({'purchase_ok': 1})
                    vendor = self.env['res.partner'].search([('name','=',lines[1])],limit=1)
                    if not vendor:
                        vendor = self.env['res.partner'].create({
                            'name': lines[1],
                            })

                    supplierinfo = self.env['product.supplierinfo'].search([('name','=',vendor.id),('product_tmpl_id','=',product.id)])
                    if not supplierinfo:
                        supplierinfo = self.env['product.supplierinfo'].create({
                            'name': vendor.id,
                            'product_tmpl_id': product.id, 
                            'price': cost,
                            'min_qty': 1,
                            'currency_id': self.env.ref('base.USD').id,
                            })

                    supplierinfo.write({'company_id': False})


                if lines[9]:
                    sh = lines[9]
                    if 'EUR ' in sh:
                        sh = sh.replace('EUR ','')

                    if '$ ' in sh:
                        sh = sh.replace('$ ','')

                    companies = self.env['res.company'].search([('is_region','=',1)])
                    for company in companies:
                        price_sh = self.env.ref('base.USD')._convert(float(sh),company.currency_id,company,date)
                        shipping_price = self.env['shipping.price'].sudo().search([('product_id','=',product.id),('company_id','=',company.id),('carrier_id','=',2),('price','=',price_sh)])
                        if not shipping_price:
                            shipping_price = self.env['shipping.price'].sudo().create({
                                'product_id': product.id,
                                'company_id': company.id,
                                'carrier_id': 2,
                                'price': price_sh
                                })

                        product.product_variant_ids._change_standard_price_company(cost, company)

                if lines[19] == 'Yes':
                    taxes.append(1013)

                #if lines[20] == 'Yes':
                    #taxes.append(74)

                if lines[21] == 'Yes':
                    taxes.append(1040)

                if lines[22] == 'Yes':
                    taxes.append(1066)

                if lines[23] == 'Yes':
                    taxes.append(1064)

                if lines[24] == 'Yes':
                    taxes.append(1076)

                if lines[25] == 'Yes':
                    taxes.append(1077)

                if lines[26] == 'Yes':
                    taxes.append(1078)

                if lines[27] == 'Yes':
                    taxes.append(1081)

                if lines[28] == 'Yes':
                    taxes.append(1050)

                if lines[29] == 'Yes':
                    taxes.append(1049)

                if lines[30] == 'Yes':
                    taxes.append(1043)

                if lines[31] == 'Yes':
                    taxes.append(1047)

                if lines[32] == 'Yes':
                    taxes.append(1295)

                if lines[33] == 'Yes':
                    taxes.append(1007)

                if lines[34] == 'Yes':
                    taxes.append(1045)


                if lines[35] == 'Yes':
                    taxes.append(1059)

                if lines[36] == 'Yes':
                    taxes.append(1001)

                if lines[37] == 'Yes':
                    taxes.append(1068)

                if lines[38] == 'Yes':
                    taxes.append(964)

                if lines[39] == 'Yes':
                    taxes.append(963)

                if lines[40] == 'Yes':
                    taxes.append(962)

                if lines[41] == 'Yes':
                    taxes.append(1020)

                if lines[42] == 'Yes':
                    taxes.append(960)

                if lines[43] == 'Yes':
                    taxes.append(1017)

                product.write({'taxes_id': [(6, 0, taxes)]})

                if lines[8]:
                    value_id = self.env['product.attribute.value'].search([('name','=',lines[8])])
                    if value_id:
                        attribute_line = self.env['product.template.attribute.line'].create({
                            'attribute_id': 1,
                            'product_tmpl_id': product.id,
                            'value_ids': [(6, 0, [value_id.id])],
                        })
                    
                        product.write({'attribute_line_ids': [(6, False, [attribute_line.id])]})

                companies = self.env['res.company'].search([('is_region','=',False)])
                for company in companies:
                    company_price = self.env['company.price'].search([('company_id','=',company.id),('product_tmpl_id','=',product.id)])
                    if not company_price:
                        company_price = self.env['company.price'].create({
                            'company_id': company.id,
                            'product_tmpl_id': product.id,
                            'price': price,
                            })
                        company_price._compute_local_price()

        offset.write({'value': str(new_value)})

                #product.generate_price()


    def import_europe_products(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            lines = row.split('\t')
            if lines[8]:
                price = False
                cost = False
                is_pack = False
                if lines[7] == 'Package':
                    is_pack = True

                product_name = lines[0].strip()
                taxes = []
                product = self.env['product.template'].search([('name','=',product_name),('product_type','=',lines[7])],limit=1)
                vendor = False
                product_category = False                

                if lines[6]:
                    product_category = self.env['product.category'].search([('name','=',lines[6])])
                    if not product_category:
                        product_category = self.env['product.category'].create({
                            'name': lines[6]
                            })


                if lines[4]:
                    cost = lines[4]
                    if "," in cost:
                        cost = cost.replace(",","")

                    cost = float(cost)

                if lines[5]:
                    price = lines[5]
                    if "," in price:
                        price = price.replace(",","")

                    try:
                        price = float(price)

                    except:
                        price = 0

                if not product:
                    product = self.env['product.template'].create({
                        'name': product_name,
                        'standard_price': cost,
                        'lst_price': price,
                        'product_type': lines[7],
                        'categ_id': product_category.id if product_category else self.env.ref('product.product_category_all').id,
                        'description_sale': lines[10],
                        'description': lines[16],
                        'is_pack': is_pack,
                        'sale_ok': 1,
                        })

                if lines[1]:
                    product.write({'purchase_ok': 1})
                    vendor = self.env['res.partner'].search([('name','=',lines[1])],limit=1)
                    if not vendor:
                        vendor = self.env['res.partner'].create({
                            'name': lines[1],
                            })

                    supplierinfo = self.env['product.supplierinfo'].search([('name','=',vendor.id),('product_tmpl_id','=',product.id)])
                    if not supplierinfo:
                        supplierinfo = self.env['product.supplierinfo'].create({
                            'name': vendor.id,
                            'product_tmpl_id': product.id, 
                            'price': cost,
                            'min_qty': 1,
                            'currency_id': self.env.ref('base.USD').id,
                            })

                    supplierinfo.write({'company_id': False})


                if lines[9]:
                    sh = lines[9]
                    if 'EUR ' in sh:
                        sh = sh.replace('EUR ','')

                    if '$ ' in sh:
                        sh = sh.replace('$ ','')

                    if '$' in sh:
                        sh = sh.replace('$','')

                    companies = self.env['res.company'].search([('is_region','=',1)])
                    for company in companies:
                        price_sh = self.env.ref('base.USD')._convert(float(sh),company.currency_id,company,date)
                        shipping_price = self.env['shipping.price'].sudo().search([('product_id','=',product.id),('company_id','=',company.id),('carrier_id','=',2),('price','=',price_sh)])
                        if not shipping_price:
                            shipping_price = self.env['shipping.price'].sudo().create({
                                'product_id': product.id,
                                'company_id': company.id,
                                'carrier_id': 2,
                                'price': price_sh
                                })

                if lines[18] == 'Yes':
                    taxes.append(74)
                    taxes.append(73)

                product.write({'taxes_id': [(6, 0, taxes)]})

                if lines[8]:
                    value_id = self.env['product.attribute.value'].search([('name','=',lines[8])])
                    if value_id:
                        attribute_line = self.env['product.template.attribute.line'].create({
                            'attribute_id': 1,
                            'product_tmpl_id': product.id,
                            'value_ids': [(6, 0, [value_id.id])],
                        })
                    
                        product.write({'attribute_line_ids': [(6, False, [attribute_line.id])]})

                companies = self.env['res.company'].browse(1131)
                for company in companies:
                    company_price = self.env['company.price'].search([('company_id','=',company.id),('product_tmpl_id','=',product.id)])
                    if not company_price:
                        company_price = self.env['company.price'].create({
                            'company_id': company.id,
                            'product_tmpl_id': product.id,
                            'price': price,
                            })
                        company_price._compute_local_price()

                #product.generate_price()




    def import_packs(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            price = False
            cost = False
            lines = row.split('\t')
            product_type = 'product'
            #raise ValidationError(lines[44])

            if lines[4] == 'No':
                product_type = 'service'

            package_name = lines[3].strip()
            package = self.env['product.template'].search([('name','=',package_name)],limit=1)
            if not package:
                package = self.env['product.template'].search([('name','ilike',package_name)],limit=1)

            if package:
                package.write({'type': product_type})

                product_name = lines[1].strip()
                product = self.env['product.product'].search([('name','=',product_name)],limit=1)
                if not product:

                    product = self.env['product.product'].create({
                        'name': product_name,
                        'sale_ok': 0,
                        'purchase_ok': 0,
                        'type': product_type,
                        'categ_id': package.categ_id.id,
                        #'description_sale': lines[4],
                        #'description': lines[6],
                        })

                    if lines[2]:
                        name_translation = self.env['ir.translation'].search([('lang','=','ar_SY'),('name','=','product.product,name'),('res_id','=',product.id),('type','=','model')],limit=1)
                        if not name_translation:
                            name_translation = self.env['ir.translation'].create({
                                'src': product_name,
                                'value': lines[2],
                                'name': 'product.product,name',
                                'lang': 'ar_SY',
                                'type': 'model',
                                'state': 'translated',
                                'res_id': product.id,
                                })

                        else:
                            name_translation.write({
                                'value': lines[2],
                                'state': 'translated',
                                })

                if package:
                    packLine = self.env['product.pack'].search([('product_id','=',product.id),('bi_product_template','=',package.id)])
                    if not packLine:
                        packLine = self.env['product.pack'].create({
                            'product_id': product.id,
                            'qty_uom': 1,
                            'bi_product_template': package.id,
                            })

                    package.write({'is_pack': True})

    def import_europe_packs(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            price = False
            cost = False
            lines = row.split('\t')
            product_type = 'product'
            #raise ValidationError(lines[44])

            if lines[3] == 'No':
                product_type = 'service'


            package_name = lines[2].strip()
            package = self.env['product.template'].search([('name','=',package_name)],limit=1)
            if not package:
                package = self.env['product.template'].search([('name','ilike',package_name)],limit=1)

            if package:
                package.write({'type': product_type})

                product = self.env['product.product'].search([('name','=',lines[1])],limit=1)
                if not product:

                    product = self.env['product.product'].create({
                        'name': lines[1],
                        'sale_ok': 0,
                        'purchase_ok': 0,
                        'type': product_type,
                        'categ_id': package.categ_id.id,
                        })

                if package:
                    packLine = self.env['product.pack'].search([('product_id','=',product.id),('bi_product_template','=',package.id)])
                    if not packLine:
                        packLine = self.env['product.pack'].create({
                            'product_id': product.id,
                            'qty_uom': 1,
                            'bi_product_template': package.id,
                            })

                    package.write({'is_pack': True})

    def import_live_products(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            price = False
            cost = False
            lines = row.split('\t')
            #raise ValidationError(lines[44])
            is_pack = False
            taxes = []
            course_name = lines[0].strip()
            course = self.env['course'].search([('name','=',course_name),('mrm_id','>',0)],limit=1)
            if not course:
                course = self.env['course'].search([('name','ilike',course_name),('mrm_id','>',0)],limit=1)
                if not course:
                    course = self.env['course'].search([('name','ilike',course_name)],limit=1)

            if lines[8] != 'Self Study':
                vendor = False
                product_category = False                

                if lines[6]:
                    program = self.env['program'].search([('name','=',lines[6])],limit=1)
                    if not program:
                        program = self.env['program'].create({
                            'name': lines[6]
                            })
                """if lines[2]:
                    image_full_path = "http://top-finance.net/odoo_mrm/"
                    image_full_path += lines[2]
                    if image_full_path:
                        if ".jpg" not in image_full_path and "jpg" in image_full_path:
                            image_full_path = image_full_path.replace("jpg",".jpg")
                        try:
                            response = requests.get(image_full_path)
                            image_base64 = base64.b64encode(response.content)
                        except:
                            print("error")"""
                
                if not course:

                    course = self.env['course'].create({
                        'name': course_name,
                        #'image': image_base64,
                        'program_id': program.id if program else False,
                        'description': lines[10],
                        })

                #else:
                    #course.write({'image': image_base64})

                if lines[3]:
                    name_translation = self.env['ir.translation'].search([('src','=',course_name),('lang','=','ar_SY'),('name','=','course,name')],limit=1)
                    if not name_translation:
                        name_translation = self.env['ir.translation'].create({
                            'src': course_name,
                            'value': lines[3],
                            'name': 'course,name',
                            'lang': 'ar_SY',
                            'type': 'model',
                            'state': 'translated'
                            })

                    else:
                        name_translation.write({
                            'value': lines[3],
                            'state': 'translated',
                            })

                    cost = float(cost)

                if lines[5]:
                    price = lines[5]
                    if "," in price:
                        price = price.replace(",","")

                    if "CAD  " in price:
                        price = price.replace("CAD  ","")

                    price = float(price)

                if lines[11]:
                    desc_translation = self.env['ir.translation'].search([('src','=',lines[10]),('lang','=','ar_SY'),('name','=','course,description')],limit=1)
                    if not desc_translation:
                        desc_translation = self.env['ir.translation'].create({
                            'src': lines[10],
                            'value': lines[11],
                            'name': 'course,description',
                            'lang': 'ar_SY',
                            'type': 'model',
                            'state': 'translated'
                            })

                    else:
                        desc_translation.write({
                            'value': lines[11],
                            'state': 'translated'
                            })

                if lines[19] == 'Yes':
                    taxes.append(1)

                #if lines[20] == 'Yes':
                    #taxes.append(74)

                if lines[21] == 'Yes':
                    taxes.append(49)

                if lines[22] == 'Yes':
                    taxes.append(3)

                if lines[23] == 'Yes':
                    taxes.append(3)

                if lines[24] == 'Yes':
                    taxes.append(51)

                if lines[25] == 'Yes':
                    taxes.append(51)

                if lines[26] == 'Yes':
                    taxes.append(51)

                if lines[28] == 'Yes':
                    taxes.append(53)

                if lines[29] == 'Yes':
                    taxes.append(53)

                if lines[30] == 'Yes':
                    taxes.append(53)

                if lines[31] == 'Yes':
                    taxes.append(53)

                if lines[32] == 'Yes':
                    taxes.append(53)

                if lines[33] == 'Yes':
                    taxes.append(53)

                if lines[34] == 'Yes':
                    taxes.append(53)


                if lines[35] == 'Yes':
                    taxes.append(55)

                if lines[36] == 'Yes':
                    taxes.append(57)

                if lines[37] == 'Yes':
                    taxes.append(59)

                if lines[38] == 'Yes':
                    taxes.append(61)

                if lines[39] == 'Yes':
                    taxes.append(63)

                if lines[40] == 'Yes':
                    taxes.append(65)

                if lines[41] == 'Yes':
                    taxes.append(67)

                if lines[42] == 'Yes':
                    taxes.append(69)

                if lines[43] == 'Yes':
                    taxes.append(71)


                companies = self.env['res.company'].search([('parent_id','=',False),('id','!=',1131)])
                for company in companies:
                    taxes_array = []
                    company_taxes = self.env['account.tax'].search([('company_id','=',company.id)])
                    if company_taxes:
                        for company_tax in company_taxes:
                            if company_tax.id in taxes:
                                taxes_array.append(company_tax.id)

                    company_price = self.env['company.price'].search([('course_id','=',course.id),('company_id','=',company.id)])
                    if not company_price:
                        company_price = self.env['company.price'].create({
                            'course_id': course.id,
                            'company_id': company.id,
                            'tax_ids': [(6, 0, taxes_array)]
                            })
                    else:
                        company_price.write({
                            'course_id': course.id,
                            'company_id': company.id,
                            'tax_ids': [(6, 0, taxes_array)]
                            })

                    course_ticket = self.env['course.ticket.price'].sudo().search([('name','=','Regular'),('ticket_id','=',company_price.id)])
                    if(not course_ticket):
                        course_ticket = self.env['course.ticket.price'].sudo().create({
                            'name': 'Regular',
                            'ticket_id': company_price.id,
                            'price': 0,
                            })
                    else:
                        course_ticket.sudo().write({
                            'name': 'Regular',
                            'ticket_id': company_price.id,
                            'price': 0,
                            })

        return True

    def import_live_europe_products(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            price = False
            cost = False
            lines = row.split('\t')
            #raise ValidationError(lines[44])
            is_pack = False
            taxes = []
            course_name = lines[0].strip()
            course = self.env['course'].search([('name','=',course_name),('mrm_id','>',0)],limit=1)
            if not course:
                course = self.env['course'].search([('name','=',course_name)],limit=1)

            if lines[8] != 'Self Study':
                vendor = False
                product_category = False                

                if lines[6]:
                    program = self.env['program'].search([('name','=',lines[6])],limit=1)
                    if not program:
                        program = self.env['program'].create({
                            'name': lines[6]
                            })
                """if lines[2]:
                    image_full_path = "http://top-finance.net/odoo_mrm/"
                    image_full_path += lines[2]
                    if image_full_path:
                        if ".jpg" not in image_full_path and "jpg" in image_full_path:
                            image_full_path = image_full_path.replace("jpg",".jpg")
                        try:
                            response = requests.get(image_full_path)
                            image_base64 = base64.b64encode(response.content)
                        except:
                            print("error")"""
                
                if not course:

                    course = self.env['course'].create({
                        'name': course_name,
                        #'image': image_base64,
                        'program_id': program.id if program else False,
                        'description': lines[10],
                        })

                #else:
                    #course.write({'image': image_base64})

                if lines[3]:
                    name_translation = self.env['ir.translation'].search([('src','=',course_name),('lang','=','ar_SY'),('name','=','course,name')],limit=1)
                    if not name_translation:
                        name_translation = self.env['ir.translation'].create({
                            'src': course_name,
                            'value': lines[3],
                            'name': 'course,name',
                            'lang': 'ar_SY',
                            'type': 'model',
                            'state': 'translated'
                            })

                    else:
                        name_translation.write({
                            'value': lines[3],
                            'state': 'translated',
                            })

                if lines[4]:
                    cost = lines[4]
                    if "," in cost:
                        cost = cost.replace(",","")

                    cost = float(cost)

                if lines[5]:
                    price = lines[5]
                    if "," in price:
                        price = price.replace(",","")

                    try:
                        price = float(price)

                    except:
                        price = 0

                if lines[18] == 'Yes':
                    taxes.append(74)
                    taxes.append(73)


                
                canda_company = self.env['res.company'].browse(1131)
                canada_taxes_array = []
                canada_taxes = self.env['account.tax'].search([('parent_company_id','=',1131)])
                for canada_tax in canada_taxes:
                    if 18 in taxes or 24 in taxes or 14 in taxes or 16 in taxes or 20 in taxes or 22 in taxes or 26 in taxes or 28 in taxes:
                        canada_taxes_array.append(canada_tax.id)
                    
                company_price = self.env['company.price'].search([('course_id','=',course.id),('company_id','=',1131)])
                if not company_price:
                    company_price = self.env['company.price'].create({
                        'course_id': course.id,
                        'company_id': 1131,
                        'tax_ids': [(6, 0, canada_taxes_array)]
                        })

                else:
                    company_price.write({
                        'course_id': course.id,
                        'company_id': 1131,
                        'tax_ids': [(6, 0, canada_taxes_array)]
                        })

                course_ticket = self.env['course.ticket.price'].sudo().search([('name','=','Regular'),('ticket_id','=',company_price.id)])
                if(not course_ticket):
                    course_ticket = self.env['course.ticket.price'].sudo().create({
                        'name': 'Regular',
                        'ticket_id': company_price.id,
                        'price': 0,
                        })
                else:
                    course_ticket.sudo().write({
                        'name': 'Regular',
                        'ticket_id': company_price.id,
                        'price': 0,
                        })

        return True


    def import_live_packs(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            price = False
            cost = False
            lines = row.split('\t')
            product_type = 'product'
            products = []
            #raise ValidationError(lines[44])

            if lines[4] == 'No':
                product_type = 'service'

            course_name = lines[3].strip()
            course = self.env['course'].search([('name','=',course_name),('mrm_id','>',0)],limit=1)
            if not course:
                course = self.env['course'].search([('name','ilike',course_name),('mrm_id','>',0)],limit=1)

            if not course:
                course = self.env['course'].search([('name','ilike',course_name)],limit=1)

            if course:
                product = self.env['product.product'].search([('name','=',course_name)],limit=1)
                if product:
                    #raise ValidationError(course_name)

                    products.append(product.product_tmpl_id.id)
                    for company_price in course.company_prices:
                        for ticket in company_price.ticket_ids:
                            ticket.write({'mapped_item_ids': [(6, 0, products)] })

                #course.generate_price()

    def import_live_europe_packs(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            price = False
            cost = False
            lines = row.split('\t')
            product_type = 'product'
            products = []
            #raise ValidationError(lines[44])

            if lines[3] == 'No':
                product_type = 'service'


            course_name = lines[2].strip()
            course = self.env['course'].search([('name','=',course_name)],limit=1)

            if not course:
                course = self.env['course'].search([('name','ilike',course_name),('mrm_id','>',0)],limit=1)

            if not course:
                course = self.env['course'].search([('name','ilike',course_name)],limit=1)

            if course:                
                product = self.env['product.product'].search([('name','=',course_name)],limit=1)
                if product:
                    products.append(product.product_tmpl_id.id)
                    for company_price in course.company_prices:
                        for ticket in company_price.ticket_ids:
                            ticket.write({'mapped_item_ids': [(6, 0, products)]})

                #course.generate_price()

    def fix_images(self):
        offset = self.env['ir.config_parameter'].browse(43)
        value = offset.value
        new_value = int(value) + 100
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        if new_value > len(reader):
            new_value = len(reader)
        for i in range(int(value), new_value):
            lines = reader[i].split('\t')
            product_name = lines[0].strip()
            product = self.env['product.template'].search([('name','=',product_name),('product_type','=',lines[7])],limit=1)

            if lines[2]:
                image_name = lines[2].strip()
                image_full_path = "http://top-finance.net/odoo_mrm/"                

                image_full_path += image_name
                #raise ValidationError(image_full_path)
                if image_full_path:
                    if ".jpg" not in image_full_path and "jpg" in image_full_path:
                        image_full_path = image_full_path.replace("jpg",".jpg")

                    try:
                        response = requests.get(image_full_path)
                        image_base64 = base64.b64encode(response.content)
                        product.write({'image_1920': image_base64})

                    except:
                        print("error")

        offset.write({'value': str(new_value)})


    def fix_sales_desc(self):
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            price = False
            cost = False
            lines = row.split(',')
            raise ValidationError(lines)


    def fix_cost(self):
        date = datetime.now().strftime('%Y-%m-%d')
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            cost = False
            lines = row.split('\t')
            if lines[4]:
                cost = lines[4]
                if "," in cost:
                    cost = cost.replace(",","")
                cost = float(cost)
            
            
            product_name = lines[0].strip()
            product = self.env['product.template'].search([('name','=',product_name),('product_type','=',lines[7])],limit=1)
            companies = self.env['res.company'].search([])
            for company in companies:
                product.product_variant_ids._change_standard_price_company(cost, company)



    def fix_translation(self):
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            lines = row.split('\t')

            product_name = lines[0].strip()
            product = self.env['product.template'].search([('name','=',product_name),('product_type','=',lines[7])],limit=1)

            if lines[3]:
                name_translation = self.env['ir.translation'].search([('lang','=','ar_SY'),('name','=','product.template,name'),('res_id','=',product.id),('type','=','model')],limit=1)
                if not name_translation:
                    name_translation = self.env['ir.translation'].create({
                        'src': product_name,
                        'value': lines[3],
                        'name': 'product.template,name',
                        'lang': 'ar_SY',
                        'type': 'model',
                        'state': 'translated',
                        'res_id': product.id,
                        })
                else:
                    name_translation.write({
                        'value': lines[3],
                        'state': 'translated',
                        })

            if lines[11]:
                desc_translation = self.env['ir.translation'].search([('lang','=','ar_SY'),('name','=','product.template,description_sale'),('res_id','=',product.id),('type','=','model')],limit=1)
                if not desc_translation:
                    desc_translation = self.env['ir.translation'].create({
                        'src': lines[10],
                        'value': lines[11],
                        'name': 'product.template,description_sale',
                        'lang': 'ar_SY',
                        'type': 'model',
                        'state': 'translated',
                        'res_id': product.id
                        })
                else:
                    desc_translation.write({
                        'value': lines[11],
                        'state': 'translated'
                        })


    def fix_packs_translation(self):
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        for row in reader:
            lines = row.split('\t')
            package = self.env['product.template'].search([('name','=',lines[2])],limit=1)

            product_name = lines[0].strip()
            if package:
                product = self.env['product.product'].search([('name','=',product_name)],limit=1)

                if lines[1]:
                    name_translation = self.env['ir.translation'].search([('lang','=','ar_SY'),('name','=','product.product,name'),('res_id','=',product.id),('type','=','model')],limit=1)
                    if not name_translation:
                        name_translation = self.env['ir.translation'].create({
                            'src': product_name,
                            'value': lines[1],
                            'name': 'product.product,name',
                            'lang': 'ar_SY',
                            'type': 'model',
                            'state': 'translated',
                            'res_id': product.id,
                            })
                    else:
                        name_translation.write({
                            'value': lines[1],
                            'state': 'translated',
                            })
                if lines[5]:
                    desc_translation = self.env['ir.translation'].search([('lang','=','ar_SY'),('name','=','product.product,description_sale'),('res_id','=',product.id),('type','=','model')],limit=1)
                    if not desc_translation:
                        desc_translation = self.env['ir.translation'].create({
                            'src': lines[4],
                            'value': lines[5],
                            'name': 'product.product,description_sale',
                            'lang': 'ar_SY',
                            'type': 'model',
                            'state': 'translated',
                            'res_id': product.id,
                            })
                    else:
                        desc_translation.write({
                            'value': lines[5],
                            'state': 'translated'
                            })


    def fix_study_format(self):
        attachment = self.env['ir.attachment'].browse(self.id)
        objFile = str(base64.b64decode(attachment.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        formats = {
        'Self Study': 'self',
        'All': 'all',
        'Live': 'live',
        'Live Online': 'liveonline',
        'Live online': 'liveonline',
        'live': 'live',
        }
        for row in reader:
            lines = row.split('\t')
            product_name = lines[0].strip()
            product = self.env['product.template'].search([('name','=',product_name),('product_type','=',lines[7])],limit=1)
            product.write({'study_format': formats[lines[8].strip()]})

    def update_product_taxes(self):
        offset = self.env['ir.config_parameter'].browse(43)
        date = datetime.now().strftime('%Y-%m-%d')
        value = offset.value
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        new_value = int(value) + 100
        if new_value > len(reader):
            new_value = len(reader)

        for i in range(int(value), new_value):
            lines = reader[i].split('\t')
            if lines[8]:
                price = False
                cost = False
                is_pack = False
                if lines[7] == 'Package':
                    is_pack = True

                if lines[5]:
                    price = lines[5]
                    if "," in price:
                        price = price.replace(",","")

                    if "CAD  " in price:
                        price = price.replace("CAD  ","")

                    price = float(price)

                
                product_name = lines[0].strip()

                taxes = []
                product = self.env['product.template'].search([('name','=',product_name),('product_type','=',lines[7])],limit=1)

                if lines[19] == 'Yes':
                    taxes.append(1013)

                #if lines[20] == 'Yes':
                    #taxes.append(74)

                if lines[21] == 'Yes':
                    taxes.append(1040)

                if lines[22] == 'Yes':
                    taxes.append(1066)

                if lines[23] == 'Yes':
                    taxes.append(1064)

                if lines[24] == 'Yes':
                    taxes.append(1076)

                if lines[25] == 'Yes':
                    taxes.append(1077)

                if lines[26] == 'Yes':
                    taxes.append(1078)

                if lines[27] == 'Yes':
                    taxes.append(1081)

                if lines[28] == 'Yes':
                    taxes.append(1050)

                if lines[29] == 'Yes':
                    taxes.append(1049)

                if lines[30] == 'Yes':
                    taxes.append(1043)

                if lines[31] == 'Yes':
                    taxes.append(1047)

                if lines[32] == 'Yes':
                    taxes.append(1295)

                if lines[33] == 'Yes':
                    taxes.append(1007)

                if lines[34] == 'Yes':
                    taxes.append(1045)


                if lines[35] == 'Yes':
                    taxes.append(1059)

                if lines[36] == 'Yes':
                    taxes.append(1001)

                if lines[37] == 'Yes':
                    taxes.append(1068)

                if lines[38] == 'Yes':
                    taxes.append(964)

                if lines[39] == 'Yes':
                    taxes.append(963)

                if lines[40] == 'Yes':
                    taxes.append(962)

                if lines[41] == 'Yes':
                    taxes.append(1020)

                if lines[42] == 'Yes':
                    taxes.append(960)

                if lines[43] == 'Yes':
                    taxes.append(1017)
                    

                product.write({'taxes_id': [(6, 0, taxes)]})

                companies = self.env['res.company'].search([('is_region','=',False)])
                for company in companies:
                    price_taxes = self.env['account.tax'].search([('id','in',taxes),('company_id.parent_id','=',company.id)])

                    company_price = self.env['company.price'].search([('company_id','=',company.id),('product_tmpl_id','=',product.id),('product_tmpl_id','!=',False)])
                    if not company_price:
                        company_price = self.env['company.price'].create({
                            'company_id': company.id,
                            'product_tmpl_id': product.id,
                            'price': price,
                            'tax_ids': [(6, 0, price_taxes.ids)] if price_taxes else [(5, 0, 0)]
                            })
                        company_price._compute_local_price()

                    else:
                        company_price.write({
                            'tax_ids': [(6, 0, price_taxes.ids)] if price_taxes else [(5, 0, 0)]
                            })
                        if company_price.price == 0 or not company_price.price:
                            company_price.write({'price': price})
                        company_price._compute_local_price()

        offset.write({'value': str(new_value)})

