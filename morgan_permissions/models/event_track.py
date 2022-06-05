
from odoo import api, models,fields,_
from odoo.exceptions import ValidationError


class EventTrack(models.Model):
	_inherit = "event.track"

	def action_archive(self):
		if not self.env.user.has_group('morgan_permissions.super_user_group') and not self.env.user.has_group('morgan_permissions.master_operation_group'):
			raise ValidationError("only super user and master operation can perform this action")

		return super(EventTrack, self).action_archive()