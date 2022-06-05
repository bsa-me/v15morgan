from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    background_image_certification = fields.Binary()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            background_image_certification=self.env['ir.config_parameter'].sudo().get_param(
                'education_reports.background_image_certification'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        param.set_param('education_reports.background_image_certification', self.background_image_certification)
