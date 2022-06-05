from odoo import models, fields


class PartnerBank(models.Model):
	_inherit = "res.partner.bank"
	swift_code = fields.Char('Swift Code')
	iban = fields.Char('IBAN')