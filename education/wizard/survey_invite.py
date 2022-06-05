# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields,api

class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    @api.onchange('survey_id')
    def onchange_survey(self):
    	if self.survey_id:
    		if self.survey_id.event_id:
    			registration_ids = self.survey_id.event_id.registration_ids.mapped('partner_id').ids

    			self.partner_ids = [(6, 0, registration_ids)]
