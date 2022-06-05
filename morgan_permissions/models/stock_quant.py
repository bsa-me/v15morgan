
from odoo import api, models,fields,_


class Quant(models.Model):
	_inherit = "stock.quant"

	is_master_accountant = fields.Boolean(compute="_compute_user_groups")
	is_normal_accountant = fields.Boolean(compute="_compute_user_groups")
	is_master_operation = fields.Boolean(compute="_compute_user_groups")
	is_normal_operation = fields.Boolean(compute="_compute_user_groups")
	is_master_marketing = fields.Boolean(compute="_compute_user_groups")
	is_normal_marketing = fields.Boolean(compute="_compute_user_groups")
	is_master_commercial = fields.Boolean(compute="_compute_user_groups")
	is_ro_staff = fields.Boolean(compute="_compute_user_groups")
	is_head_of_hub = fields.Boolean(compute="_compute_user_groups")
	is_business_manager = fields.Boolean(compute="_compute_user_groups")
	is_program_advisor = fields.Boolean(compute="_compute_user_groups")
	is_city_operations = fields.Boolean(compute="_compute_user_groups")
	is_admin = fields.Boolean(compute="_compute_user_groups")
	is_ecommerce = fields.Boolean(compute="_compute_user_groups")

	def _compute_user_groups(self):
		for record in self:
			record['is_master_accountant'] = False
			record['is_normal_accountant'] = False
			record['is_master_operation'] = False
			record['is_normal_operation'] = False
			record['is_master_marketing'] = False
			record['is_normal_marketing'] = False
			record['is_master_commercial'] = False
			record['is_ro_staff'] = False
			record['is_head_of_hub'] = False
			record['is_business_manager'] = False
			record['is_program_advisor'] = False
			record['is_city_operations'] = False
			record['is_admin'] = False
			record['is_ecommerce'] = False

			if self.env.user.has_group('morgan_permissions.master_accountant_group'):
				record['is_master_accountant'] = True

			if self.env.user.has_group('morgan_permissions.normal_accountant_group'):
				record['is_normal_accountant'] = True

			if self.env.user.has_group('morgan_permissions.master_operation_group'):
				record['is_master_operation'] = True

			if self.env.user.has_group('morgan_permissions.normal_operation_group'):
				record['is_normal_operation'] = True

			if self.env.user.has_group('morgan_permissions.master_marketing_group'):
				record['is_master_marketing'] = True

			if self.env.user.has_group('morgan_permissions.normal_marketing_group'):
				record['is_normal_marketing'] = True
			
			if self.env.user.has_group('morgan_permissions.master_commercial_group'):
				record['is_master_commercial'] = True

			if self.env.user.has_group('morgan_permissions.ro_staff_group'):
				record['is_ro_staff'] = True

			if self.env.user.has_group('morgan_permissions.head_of_hub_group'):
				record['is_head_of_hub'] = True

			if self.env.user.has_group('morgan_permissions.business_manager_group'):
				record['is_business_manager'] = True

			if self.env.user.has_group('morgan_permissions.program_advisor_group'):
				record['is_program_advisor'] = True

			if self.env.user.has_group('morgan_permissions.city_operations_group'):
				record['is_city_operations'] = True

			if self.env.user.has_group('morgan_permissions.admin_group'):
				record['is_admin'] = True

			if self.env.user.has_group('morgan_permissions.ecommerce_group'):
				record['is_ecommerce'] = True