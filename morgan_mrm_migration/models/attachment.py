import base64
from datetime import timedelta,datetime
from odoo import models, fields, api
from odoo.exceptions import UserError
import xlrd
import string
from zipfile import ZipFile
from openpyxl import load_workbook
import dateparser
from dateutil.parser import parse


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    def fix_duplicated_receipts(self):
        payment_types = {
        'Bank Transfer': 'transfer',
        'Cash': 'cash',
        'Cheque': 'cheque',
        'Converted FP (Void)': 'cash',
        'Credit/Debit Card': 'credit_card',
        }
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 100
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True


        for i in range(count, new_value):
            lines = reader[i].split('\t')
            vals = {}
            vals['from_mrm'] = True
            vals['partner_type'] = 'customer'
            vals['payment_method_id'] = self.env.ref('account.account_payment_method_manual_in').id

            if lines[1]:
                partner = self.env['res.partner'].search([('mrm_id','=',lines[1]),('is_mrm_contact','=',False)],limit=1)
                if not partner:
                    partner = self.env['res.partner'].search([('name','=',lines[0]),('is_mrm_contact','=',False)],limit=1)


                vals['partner_id'] = partner.id
                vals['name'] = lines[2]


                payment_date = lines[3]
                payment_date = payment_date.replace("/", "-")
                payment_date = payment_date[:-2] + "20" + payment_date[-2:]
                payment_date = datetime.strptime(payment_date, "%m-%d-%Y")
                vals['payment_date'] = payment_date


                if lines[4]:
                    date_cleared = lines[4]
                    date_cleared = date_cleared.replace("/", "-")
                    date_cleared = date_cleared[:-2] + "20" + date_cleared[-2:]
                    date_cleared = datetime.strptime(date_cleared, "%m-%d-%Y")
                    vals['date_cleared'] = date_cleared

                #vals['invoice_ids'] = [(6, 0, [invoice.id])]

                invoice = self.env['account.move'].search([('name','=',lines[5]),('partner_id','=',partner.id)])
                if invoice:
                    invoice.button_draft()
                    if invoice.payment_ids:
                        payments = invoice.payment_ids.ids
                        self.env['register.payment'].search([('payment_id','in',payments)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})

                company = self.env['res.company'].search([('name','=',lines[13].strip())])
                if not company:
                    company = self.env['res.company'].search([('name','ilike',lines[13].strip())])
                vals['company_id'] = company.id



                vals['payment_mode'] = payment_types.get(lines[6])

                if vals['payment_mode'] == 'cash':
                    journal = self.env['account.journal'].search([('company_id','=',company.id),('type','=','cash')],limit=1)

                else:
                    journal = self.env['account.journal'].search([('company_id','=',company.id),('type','=','bank')],limit=1)

                vals['journal_id'] = journal.id

                vals['payment_ref'] = lines[7]

                currency = self.env['res.currency'].search([('name','=',lines[8])])
                vals['currency_id'] = currency.id

                amount = float(lines[9]) if lines[8] != 'USD' else float(lines[10])
                vals['amount'] = -amount if amount < 0 else amount

                vals['payment_type'] = 'inbound' if amount >= 0 else 'outbound'

                vals['comment'] = lines[11]

                payment = self.env['account.payment'].search([('name','=',vals['name']),('from_mrm','=',True),('partner_id','=',False),('state','!=','cancelled')])
                if payment:
                    self.env['register.payment'].search([('payment_id','=',payment.id)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})
                    payment.action_draft()
                    payment.write(vals)
                    payment.post()

                else:
                    payment = self.env['account.payment'].search([('name','=',vals['name']),('from_mrm','=',True),('partner_id','=',vals['partner_id']),('state','!=','cancelled')])
                    if not payment:
                        payment = self.env['account.payment'].create(vals)
                        try:
                            payment.post()

                        except:
                            raise UserError(str(vals))

                    else:
                        self.env['register.payment'].search([('payment_id','=',payment.id)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})
                        payment.action_draft()
                        payment.write(vals)
                        payment.post()



                register_payment = self.env['register.payment'].search([('payment_id','=',payment.id)])
                if not register_payment:
                    register_payment = self.env['register.payment'].create({
                        'payment_id': payment.id,
                        'partner_id': vals['partner_id'],
                        'from_mrm': True,
                        })



                payment_line = self.env['register.payment.line'].search([('payment_registration_id','=',register_payment.id)]).unlink()
                allocated_amount = float(lines[9])
                allocated_amount = -allocated_amount if allocated_amount < 0 else allocated_amount
                payment_line = self.env['register.payment.line'].create({
                    'payment_registration_id': register_payment.id,
                    'move_id': invoice.id,
                    'amount': allocated_amount,
                    'allocated_amount': allocated_amount,
                    'partner_id': vals['partner_id'],
                    })


            self.write({'processed_rows_count': new_value})

    def fix_receipts_withoutpartner(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True


        for i in range(count, new_value):
            lines = reader[i].split('\t')
            vals = {}
            receipt = self.env['account.payment'].search([('name','=',lines[0])])
            if lines[1]:
                partner = self.env['res.partner'].search([('name','=',lines[1]),('mrm_id','>',0),('is_mrm_contact','=',False)])
                if len(partner) > 1:
                    partner = self.env['res.partner'].search([('name','=',lines[1]),('mrm_id','>',0),('is_mrm_contact','=',False),('balance_invoice_ids','!=',False)],limit=1)

                if not partner and receipt.invoice_ids:
                    partner = receipt.invoice_ids[0].partner_id

                if partner:
                    receipt.write({'partner_id': partner.id})
                    items = self.env['account.move.line'].search([('move_id.name','=',receipt.name)])
                    for item in items:
                        item.write({'partner_id': partner.id})
                        self.env.cr.execute("update account_move set partner_id = " + str(partner.id) + " where id = " + str(item.move_id.id))


        self.write({'processed_rows_count': new_value})

    def fix_receipts_amount(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True


        for i in range(count, new_value):
            lines = reader[i].split('\t')
            vals = {}
            receipt = self.env['account.payment'].search([('name','=',lines[0])])
            receipt.action_draft()
            receipt.write({'amount': 0})
            receipt.post()

        self.write({'processed_rows_count': new_value})

    def fix_event_without_courses(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True


        for i in range(count, new_value):
            lines = reader[i].split('\t')
            event = self.env['event.event'].search([('mrm_id','=',lines[1])])
            course = self.env['course'].search([('mrm_id','=',lines[7]),('active','in',[True,False])])
            event.write({'course_id': course.id})

        self.write({'processed_rows_count': new_value})

    def fix_receipts_without_allocation_amount(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True


        for i in range(count, new_value):
            lines = reader[i].split('\t')
            vals = {}
            receipt = self.env['account.payment'].search([('name','=',lines[0])])
            receipt.action_draft()
            self.env['register.payment'].search([('payment_id','=',payment.id)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})
            receipt.write({'amount': 0})
            receipt.post()

        self.write({'processed_rows_count': new_value})

    def fix_receipts_allocation(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 100
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True


        for i in range(count, new_value):
            lines = reader[i].split('\t')
            vals = {}
            payment = self.env['account.payment'].search([('name','=',lines[1])])
            if len(payment) > 1:
                payment = self.env['account.payment'].search([('name','=',lines[1])], limit=1, order='id desc')

            self.env['register.payment'].search([('payment_id','=',payment.id)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})
            payment.action_draft()
            payment.write(vals)
            payment.post()

            invoice = self.env['account.move'].search([('name','=',lines[7])])
            if invoice:
                invoice.button_draft()
                if invoice.payment_ids:
                    payments = invoice.payment_ids.ids
                    self.env['register.payment'].search([('payment_id','in',payments)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})

            register_payment = self.env['register.payment'].search([('payment_id','=',payment.id)])
            if not register_payment:
                register_payment = self.env['register.payment'].create({
                    'payment_id': payment.id,
                    'partner_id': payment.partner_id.id,
                    'from_mrm': True,
                    })



            payment_line = self.env['register.payment.line'].search([('payment_registration_id','=',register_payment.id)]).unlink()
            allocated_amount = float(lines[5])
            allocated_amount = -allocated_amount if allocated_amount < 0 else allocated_amount
            payment_line = self.env['register.payment.line'].create({
                'payment_registration_id': register_payment.id,
                'move_id': invoice.id,
                'amount': allocated_amount,
                'allocated_amount': allocated_amount,
                'partner_id': payment.partner_id.id,
                })


            self.write({'processed_rows_count': new_value})

    def fix_usd_receipts(self):
        payment_types = {
        'Bank Transfer': 'transfer',
        'Cash': 'cash',
        'Cheque': 'cheque',
        'Converted FP (Void)': 'cash',
        'Credit/Debit Card': 'credit_card',
        }
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 100
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True


        for i in range(count, new_value):
            lines = reader[i].split('\t')
            vals = {}
            vals['from_mrm'] = True
            vals['partner_type'] = 'customer'
            vals['payment_method_id'] = self.env.ref('account.account_payment_method_manual_in').id

            if lines[1]:
                partner = self.env['res.partner'].search([('mrm_id','=',lines[1]),('is_mrm_contact','=',False)],limit=1)
                if not partner:
                    partner = self.env['res.partner'].search([('name','=',lines[0]),('is_mrm_contact','=',False)],limit=1)


                vals['partner_id'] = partner.id
                vals['name'] = lines[2]


                payment_date = lines[3]
                payment_date = payment_date.replace("/", "-")
                payment_date = payment_date[:-2] + "20" + payment_date[-2:]
                payment_date = datetime.strptime(payment_date, "%m-%d-%Y")
                vals['payment_date'] = payment_date


                if lines[4]:
                    date_cleared = lines[4]
                    date_cleared = date_cleared.replace("/", "-")
                    date_cleared = date_cleared[:-2] + "20" + date_cleared[-2:]
                    date_cleared = datetime.strptime(date_cleared, "%m-%d-%Y")
                    vals['date_cleared'] = date_cleared

                #vals['invoice_ids'] = [(6, 0, [invoice.id])]

                invoice = self.env['account.move'].search([('name','=',lines[5]),('partner_id','=',partner.id)])
                if invoice:
                    invoice.button_draft()
                    if invoice.payment_ids:
                        payments = invoice.payment_ids.ids
                        self.env['register.payment'].search([('payment_id','in',payments)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})

                company = self.env['res.company'].search([('name','=',lines[13].strip())])
                if not company:
                    company = self.env['res.company'].search([('name','ilike',lines[13].strip())])
                vals['company_id'] = company.id



                vals['payment_mode'] = payment_types.get(lines[6])

                if vals['payment_mode'] == 'cash':
                    journal = self.env['account.journal'].search([('company_id','=',company.id),('type','=','cash')],limit=1)

                else:
                    journal = self.env['account.journal'].search([('company_id','=',company.id),('type','=','bank')],limit=1)

                vals['journal_id'] = journal.id

                vals['payment_ref'] = lines[7]

                currency = self.env['res.currency'].search([('name','=',lines[8])])
                vals['currency_id'] = currency.id

                amount = float(lines[9]) if lines[8] != 'USD' else float(lines[10])
                vals['amount'] = -amount if amount < 0 else amount

                vals['payment_type'] = 'inbound' if amount >= 0 else 'outbound'

                vals['comment'] = lines[11]

                payment = self.env['account.payment'].search([('name','=',vals['name']),('from_mrm','=',True),('partner_id','=',False),('state','!=','cancelled')])
                if payment:
                    self.env['register.payment'].search([('payment_id','=',payment.id)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})
                    payment.action_draft()
                    payment.write(vals)
                    payment.post()

                else:
                    payment = self.env['account.payment'].search([('name','=',vals['name']),('from_mrm','=',True),('partner_id','=',vals['partner_id']),('state','!=','cancelled')])
                    if not payment:
                        payment = self.env['account.payment'].create(vals)
                        try:
                            payment.post()

                        except:
                            raise UserError(str(vals))

                    else:
                        self.env['register.payment'].search([('payment_id','=',payment.id)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})
                        payment.action_draft()
                        payment.write(vals)
                        payment.post()



                register_payment = self.env['register.payment'].search([('payment_id','=',payment.id)])
                if not register_payment:
                    register_payment = self.env['register.payment'].create({
                        'payment_id': payment.id,
                        'partner_id': vals['partner_id'],
                        'from_mrm': True,
                        })



                payment_line = self.env['register.payment.line'].search([('payment_registration_id','=',register_payment.id)]).unlink()
                allocated_amount = float(lines[9])
                allocated_amount = -allocated_amount if allocated_amount < 0 else allocated_amount
                payment_line = self.env['register.payment.line'].create({
                    'payment_registration_id': register_payment.id,
                    'move_id': invoice.id,
                    'amount': allocated_amount,
                    'allocated_amount': allocated_amount,
                    'partner_id': vals['partner_id'],
                    })


            self.write({'processed_rows_count': new_value})

    def delete_duplicated_lines(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 500
        if new_value > len(reader):
            new_value = len(reader)



            self.lines_processed = True

        for i in range(count, new_value):
            lines = reader[i].split('\t')
            move = self.env['account.move'].search([('name','=',lines[0])])
            name = 'Empty Line Item'
            if lines[3]:
                name = lines[3]

            duplicated_line = self.env['account.move.line'].search([('name','=',name),('move_id','=',move.id)],limit=1)
            if duplicated_line:
                move.button_draft()
                duplicated_line.unlink()
                move._onchange_invoice_line_ids()
                if move.payment_ids:
                    payments = move.payment_ids.ids
                    self.env['register.payment'].search([('payment_id','in',payments)]).filtered(lambda p: p.is_processed == True).write({'is_processed': False})

        self.write({'processed_rows_count': new_value})

    def fix_session_allocation(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.lines_processed = True

        for i in range(count, new_value):
            lines = reader[i].split('\t')
            if lines[5]:
                session = self.env['event.track'].search([('mrm_id','=',int(lines[5])),('employee_id','=',False)])
                instructor = False
                if lines[10]:
                    instructor = self.env['hr.employee'].search([('mrm_id','=',int(lines[10])),('active','in',[True,False])])
                    if not instructor:
                        instructor = self.env['hr.employee'].create({
                            'name': lines[9],
                            'mrm_id': lines[10],
                            'is_instructor': True
                            })
                    instructor = instructor.id

                    if instructor and session:
                        self.env.cr.execute("update event_track set employee_id = " + str(instructor) + " where id = " + str(session.id))


        self.write({'processed_rows_count': new_value})

    def import_europe_contacts(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        gender = {
        'Male': 'male',
        'Female': 'female',
        }

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True

        for i in range(count, new_value):
            lines = reader[i].split('\t')
            contact_vals = {}

            account = False
            account_vals = {}
            if lines[2]:
                try:
                    account_vals['tfrm_id'] = int(lines[2].strip())
                    account_vals['name'] = lines[3].strip()
                    account = self.env['res.partner'].search([('tfrm_id','=',account_vals['tfrm_id']),('is_mrm_contact','=',False)],limit=1)
                    if not account:
                        account = self.env['res.partner'].create(account_vals)

                    else:
                        account.write(account_vals)

                except:
                    account = False

            contact_vals['tfrm_id'] = int(lines[0].strip())
            contact_vals['name'] = lines[1].strip()
            contact_vals['is_mrm_contact'] = True
            contact_vals['parent_id'] = account.id if account else False
            contact_vals['company_type'] = 'person'
            contact_vals['account_type'] = 'b2c'

            country = False
            if lines[5]:
                country = self.env['res.country'].search([('name','=',lines[5].strip())])
                if not country:
                    country = self.env['res.country'].search([('name','ilike',lines[5].strip())],limit=1)

            if country:
                country = country.id
                contact_vals['country_id'] = country.id

            if lines[6]:
                contact_vals['gender'] = gender.get(lines[6].strip())

            contact_vals['mobile'] = lines[7]
            contact_vals['phone'] = lines[8]
            contact_vals['email'] = lines[9]
            contact_vals['job_role'] = lines[10]
            contact_vals['function'] = lines[11]

            if lines[12]:
                nationality = self.env['res.country'].search([('code','=',lines[12].strip())])
                contact_vals['nationality'] = nationality.id

            contact_vals['university'] = lines[13].strip()
            contact_vals['city'] = lines[15].strip()
            contact_vals['street'] = lines[16].strip()
            contact_vals['zip'] = lines[17].strip()
            contact_vals['company_legal_name'] = lines[18].strip()
            contact_vals['vat'] = lines[19].strip()

            if lines[20]:
                education = self.env['education.level'].search([('name','=',lines[20].strip())])
                if not education:
                    education = self.env['education.level'].create({
                        'name': lines[20]
                        })

                contact_vals['education_level'] = education.id

            contact_vals['fonction'] = lines[21].strip()
            if contact_vals['email']:
                contact_vals['email'] = contact_vals['email'] + ',' + lines[22]
            else:
                contact_vals['email'] = lines[22]


            contact_vals['street2'] = lines[23].strip()
            contact_vals['address_unit'] = lines[24].strip()
            contact_vals['comment'] = lines[25]
            contact_vals['linkedin'] = lines[26].strip()
            contact_vals['active'] = False if lines[27] == 'TRUE' else True
            contact_vals['dont_mail'] = False if lines[28] == 'FALSE' else True
            contact_vals['no_more_adds'] = '1' if lines[29] == '1' else '0'


            contact = self.env['res.partner'].search([('tfrm_id','=',contact_vals['tfrm_id']),('is_mrm_contact','=',True),('active','in',[True,False])])
            if not contact:
                contact = self.env['res.partner'].create(contact_vals)

            else:
                contact.write(contact_vals)

        self.write({'processed_rows_count': new_value})


    def import_europe_accounts(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        account_size = {
        'Small': 'small',
        'Smaal': 'small',
        'Medium': 'medium',
        'Big': 'big',
        }

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True

        for i in range(count, new_value):
            lines = reader[i].split('\t')
            account_vals = {}

            account_vals['tfrm_id'] = int(lines[0].strip())
            account_vals['name'] = lines[1].strip()
            account_vals['is_mrm_contact'] = False
            account_vals['parent_account_id'] = lines[3]
            account_vals['email'] = lines[4]
            account_vals['primary_contact_name'] = lines[5]

            if lines[6]:
                account_vals['account_size'] = account_size[lines[6].strip()]

            account_vals['organisme_collecteur'] = lines[7]
            account_vals['account_owner'] = lines[8]
            account_vals['street'] = lines[10]
            account_vals['street2'] = lines[11]
            account_vals['city'] = lines[12]

            country = False
            if lines[13]:
                country = self.env['res.country'].search([('name','=',lines[13].strip())])
                if not country:
                    country = self.env['res.country'].search([('name','ilike',lines[13].strip())],limit=1)

            if country:
                country = country.id

            account_vals['country_id'] = country

            account_vals['address_region'] = lines[14]
            account_vals['zip'] = lines[15]

            industry = False
            if lines[16]:
                industry = self.env['res.partner.industry'].search([('name','=',lines[16].strip())])
                if not industry:
                    industry = self.env['res.partner.industry'].search([('name','ilike',lines[16].strip())],limit=1)

            if industry:
                industry = industry.id

            account_vals['industry_id'] = industry
            account_vals['comment'] = lines[17]
            account_vals['vat'] = lines[18]

            if lines[19]:
                create_date = lines[19]
                create_date = create_date.replace("/", "-")
                create_date = datetime.strptime(create_date, "%d-%m-%Y")
                account_vals['mrm_create_date'] = create_date

            account = self.env['res.partner'].search([('tfrm_id','=',account_vals['tfrm_id']),('is_mrm_contact','=',False),('active','in',[True,False])])
            if not account:
                account = self.env['res.partner'].create(account_vals)

            else:
                account.write(account_vals)

        self.write({'processed_rows_count': new_value})


    def fix_first_and_last_name(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        new_value = count + 1000
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True

        for i in range(count, new_value):
            lines = reader[i].split('\t')
            if lines[0]:
                contact = self.env['res.partner'].search([('tfrm_id','=',lines[0]),('is_mrm_contact','=',True),('active','in',[True,False])])
                if contact:
                    contact.write({'first_name': lines[1], 'last_name': lines[2]})

        self.write({'processed_rows_count': new_value})

    def migrate_study_format_and_category(self):
        count = self.processed_rows_count
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()
        study_formats = {
        'Accounting': 'accounting',
        'Workshop': 'workshop',
        'workshop': 'workshop',
        'IHT': 'iht',
        'Live class': 'live',
        'Live Class': 'live',
        'Self Study': 'self',
        'Live Course': 'livecourse',
        'Live Online': 'liveonline',
        }

        new_value = count + 500
        if new_value > len(reader):
            new_value = len(reader)

            self.is_processed = True

        for i in range(count, new_value):
            lines = reader[i].split('\t')
            if lines[1]:
                invoice = self.env['account.move'].search([('name','=',lines[0].strip())],limit=1)
                if invoice:
                    category = self.env['product.category'].search([('name','=',lines[1].strip())],limit=1)
                    if not category:
                        category = self.env['product.category'].search([('name','ilike',lines[1].strip())],limit=1)

                    invoice.write({'categories': lines[1], 'study_format': lines[2]})

                    for line in invoice.line_ids:
                        if category:
                            line.write({'category_id': category.id})

                        if lines[2]:
                            line.write({'study_format': study_formats[lines[2].strip()]})


        self.write({'processed_rows_count': new_value})


    def assign_companies_countries(self):
        objFile = str(base64.b64decode(self.datas).decode('UTF-8'))
        reader = objFile.splitlines()

        for row in reader:
            lines = row.split('\t')

            company = self.env.ref(str(lines[0]))
            if lines[1]:
                country_id = self.env['res.country'].search([('name', '=', str(lines[1]))])
                if country_id:
                    if len(country_id) > 0:
                        raise UserError("Multiple results for country "+str(lines[1]))
                else:
                    raise UserError(lines[1] + " this country does not exist")
            if company:
                company.write({
                    'country_id': country_id.id,
                })
            else:
                raise UserError("Company of ref "+str(lines[0]) + " does not exist")










