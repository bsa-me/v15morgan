from odoo import fields, models

class LiveChat(models.Model):
    _inherit = 'im_livechat.channel'
    button_text = fields.Char(translate=True)
    default_message = fields.Char(translate=True)