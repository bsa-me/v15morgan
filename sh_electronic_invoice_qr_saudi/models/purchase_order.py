from odoo import api,models, fields
try:
    import qrcode
except ImportError:
    qrcode = None
import base64
import io
from num2words import num2words

class AccountMove(models.Model):
    _inherit = 'purchase.order'

    add_product_arabic_name = fields.Boolean("Add Product Arabic Name",default=True)
    sh_qr_code = fields.Text(string = "QR Code new",compute="generate_zatac_code")
    sh_qr_code_img = fields.Binary(string = "QR Code Image",compute = "compute_sh_qr_code_img")
    sh_vat = fields.Char(string="Vat",related="company_id.vat")

    amount_in_words = fields.Char(
        compute='amount_word',
        string=' Amount ',
        readonly=True,
    )
    amount_in_words_ar = fields.Char(
        compute='amount_word',
        string=' Amount arabic ',
        readonly=True,
    )
    @api.depends('amount_total')
    def amount_word(self):
        total_amount = self.amount_total        
        self.ensure_one()       
        amount_str = str('{:2f}'.format(total_amount))        
        amount_str_splt = amount_str.split('.')
        before_point_value = amount_str_splt[0]
        after_point_value = amount_str_splt[1][:2]        
        before_amount_words = num2words(int(before_point_value))
        after_amount_words = num2words(int(after_point_value))
        before_amount_ar = num2words(int(before_point_value), lang="ar")
        after_amount_ar = num2words(int(after_point_value), lang="ar")
        amount = before_amount_words
        amount_ar = before_amount_ar
        amount += ' Riyal and ' + after_amount_words + ' Halalas'
        amount_ar += ' ريال و ' + after_amount_ar + ' هللة'
        self.amount_in_words = amount.title()
        self.amount_in_words_ar = amount_ar
        
    @api.depends('amount_total', 'amount_tax', 'date_order', 'partner_id')
    def generate_zatac_code(self):
        """ Generate the qr code for Saudi e-invoicing. Specs are available at the following link at page 23
        https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/20210528_ZATCA_Electronic_Invoice_Security_Features_Implementation_Standards_vShared.pdf
        """
        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array

        for record in self:
            qr_code_str = ''
            if record.date_order and record.partner_id.vat:
                seller_name_enc = get_qr_encoding(1, record.partner_id.name)
                company_vat_enc = get_qr_encoding(2, record.partner_id.vat)
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.date_order)
                timestamp_enc = get_qr_encoding(3, time_sa.isoformat())
                invoice_total_enc = get_qr_encoding(4, str(record.amount_total))
                total_vat_enc = get_qr_encoding(5, str(record.amount_tax))

                str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
                qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            record.sh_qr_code = qr_code_str

    @api.depends('sh_qr_code')
    def compute_sh_qr_code_img(self):
        for rec in self:

            rec.sh_qr_code_img = False

            qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )

            qr.add_data(rec.sh_qr_code)
            qr.make(fit=True)

            img = qr.make_image()
            temp = io.BytesIO()
            img.save(temp, format="PNG")
            qr_code_image = base64.b64encode(temp.getvalue())
            rec.sh_qr_code_img = qr_code_image

class saudi_purchase_orderline(models.Model):
    _inherit = 'purchase.order.line'

    taxable_amount = fields.Float("Taxable Amount",compute="get_computable_tax")

    @api.depends('price_unit','product_qty')
    def get_computable_tax(self):
        for rec in self:
            rec.taxable_amount = 0.0
            if rec.price_unit and rec.product_qty:
                rec.taxable_amount = rec.price_unit * rec.product_qty