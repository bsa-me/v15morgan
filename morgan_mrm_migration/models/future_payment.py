from odoo import models, fields


class FuturePayment(models.Model):
    _inherit = 'morgan.future.payment'
    term_id = fields.Many2one('term')
    comment = fields.Text('Comments')
    from_mrm = fields.Boolean()
