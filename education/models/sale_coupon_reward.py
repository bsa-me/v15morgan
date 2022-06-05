

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class SaleCouponReward(models.Model):
	_inherit = 'coupon.reward'
	discount_apply_on = fields.Selection(selection_add=[('specific_events', 'On Specific Courses')])
	#event_ids = fields.Many2many('event.event',string='Events',domain="['|',('is_global','=',True),('company_id', '=', company_id)]")
	course_ids = fields.Many2many('course',string='Courses')
	applied_on = fields.Selection([('tuition','Tuition Fees'),('mappeditems','Mapped Items')],string='Applied On')
	condition = fields.Selection([('any','Any'),('and','And')],string='Condition')


	@api.onchange('discount_apply_on')
	def _onchange_discount_apply_on(self):
		if self.discount_apply_on == 'specific_events':
			self.applied_on = 'tuition'

		else:
			self.discount_apply_on = False

	def name_get(self):
		result = []
		for reward in self:
			reward_string = ""
			if reward.reward_type == 'product':
				reward_string = _("Free Product - %s" % (reward.reward_product_id.name))
			elif reward.reward_type == 'discount':
				if reward.discount_type == 'percentage':
					reward_percentage = str(reward.discount_percentage)
					if reward.discount_apply_on == 'on_order':
						reward_string = _("%s%% discount on total amount" % (reward_percentage))

					elif reward.discount_apply_on == 'specific_products':
						if len(reward.discount_specific_product_ids) > 1:
							reward_string = _("%s%% discount on products" % (reward_percentage))
						else:
							reward_string = _("%s%% discount on %s" % (reward_percentage, reward.discount_specific_product_ids.name))

					elif reward.discount_apply_on == 'specific_events':
						if len(reward.course_ids) > 1:
							reward_string = _("%s%% discount" % (reward_percentage))
						else:
							reward_string = _("%s%% discount on %s" % (reward_percentage, reward.course_ids.name))

					elif reward.discount_apply_on == 'cheapest_product':
						reward_string = _("%s%% discount on cheapest product" % (reward_percentage))

				elif reward.discount_type == 'fixed_amount':
					program = self.env['coupon.program'].search([('reward_id', '=', reward.id)])
					reward_string = _("%s %s discount on total amount" % (str(reward.discount_fixed_amount), program.currency_id.name))

				result.append((reward.id, reward_string))
		return result


