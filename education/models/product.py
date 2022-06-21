from odoo import api, fields, models,_
from datetime import datetime
from odoo.exceptions import UserError
import base64
from odoo.osv import expression
from odoo.tools import float_is_zero


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    program_id = fields.Many2one('program', string="Program")
    session_ok = fields.Boolean(string='Is a Session Ticket', help="If checked this product automatically "
        "creates a session registration at the sales order confirmation.")

    pricelist_item_ids = fields.One2many('product.pricelist.item','product_tmpl_id',string='Company Prices',domain=lambda self:[('is_region','=',False)])

    region_pricelist_items = fields.One2many('product.pricelist.item','product_tmpl_id',string='Prices',domain=lambda self:[('is_region','=',True)])

    product_type = fields.Selection([('Standalone','Standalone'),('Package','Package'),('Add on','Add on')])
    study_format = fields.Selection([('all','All'),('live','Live'),('liveonline','Live Online'),('self','Self Study')])

    image_id = fields.Char()

    product_tmpl_ids = fields.Many2many('product.template', 'product_related_rel', 'src_id', 'dest_id',string='Related Products')

    pack_product_ids = fields.Many2many('product.product','product_variant_rel','template_id','variant_id',string='Pack Products')

    company_prices = fields.One2many('company.price','product_tmpl_id',string="Company Prices",track_visibility='onchange',copy=True)
    region_prices = fields.One2many('company.price','product_tmpl_region_id',string="Region Prices",track_visibility='onchange',copy=True)
    registration_ids = fields.One2many('product.registration','product_tmpl_id',string='Registrations')
    registration_count = fields.Integer(compute="compute_registrations")

    attempt_count = fields.Float('Nb of attempts',compute="compute_attempt")
    passing_rate = fields.Float('Passing Rate (%)',compute="compute_attempt")
    train_to_test = fields.Float('Train to test',compute="compute_attempt")
    avg_attempt = fields.Float('Avg Attempts',compute="compute_attempt")
    is_discountable = fields.Boolean(string='Is Discountable')
    mrm_id = fields.Integer()
    tfrm_id = fields.Integer()

    def compute_registrations(self):
        for record in self:
            record['registration_count'] = len(record.registration_ids)

    @api.onchange('session_ok')
    def _onchange_session_ok(self):
        if self.session_ok:
            self.type = 'service'


    def generate_price(self):
        date = datetime.now().strftime('%Y-%m-%d')
        #self.env['company.price'].search([('product_tmpl_region_id', 'in', self.ids)]).unlink()

        if self.company_prices:
            product_taxes = []
            for company_price in self.company_prices:
                company_pricelists = self.env['product.pricelist'].sudo().search([('company_id','=',company_price.company_id.id)])
                website_pricelists = self.env['product.pricelist'].sudo().search([('website_id.company_id','=',company_price.company_id.id)])
                company_pricelists += website_pricelists
                for pricelist in company_pricelists:
                    company = False
                    if pricelist.company_id:
                        company = pricelist.company_id
                    elif pricelist.website_id.company_id:
                        company = pricelist.website_id.company_id
                    price = self.env.ref('base.USD')._convert(company_price.price,pricelist.currency_id,company,date)
                    item_vals = {}
                    item_vals['product_tmpl_id'] = self.id
                    item_vals['pricelist_id'] = pricelist.id
                    item_vals['applied_on'] = '1_product'
                    item_vals['compute_price'] = 'fixed'
                    item_vals['fixed_price'] = price
                    item_vals['min_quantity'] = 1

                    pricelist_item = self.env['product.pricelist.item'].search([('product_tmpl_id','=',self.id),('pricelist_id','=',pricelist.id)])
                    if not pricelist_item:
                        pricelist_item = self.env['product.pricelist.item'].sudo().create(item_vals)

                    else:
                        pricelist_item.sudo().write(item_vals)

                regions = company_price.company_id.region_ids
                for region in regions:

                    regionPrice = self.env['company.price'].sudo().search([('company_id','=',region.id),('product_tmpl_region_id','=',self.id)])
                    #tax_ids = self.env['account.tax'].search([('company_id','=',region.id),('id','in',company_price.tax_ids.ids)])

                    if not regionPrice:
                        company_taxes = company_price.tax_ids
                        all_taxes =  company_taxes + region.account_sale_tax_id
                        regionPrice = self.env['company.price'].sudo().create({
                            'company_id': region.id,
                            #'tax_ids': [(6, False, [region.account_sale_tax_id.id])] if region.account_sale_tax_id else [(5, 0, 0)],
                            'tax_ids': [(6, False, all_taxes.ids)],
                            'product_tmpl_region_id': self.id,
                            'price': company_price.price,
                            })
                    else:
                        all_taxes =  company_taxes + region.account_sale_tax_id
                        regionPrice.sudo().write({
                            'company_id': region.id,
                            'tax_ids': [(6, False, all_taxes.ids)],
                            #'tax_ids': [(6, False, [region.account_sale_tax_id.id])] if region.account_sale_tax_id else [(5, 0, 0)],
                            'product_tmpl_region_id': self.id,
                            'price': company_price.price,
                            })




                    regionPrice.sudo()._compute_local_price()

                    pricelists = self.env['product.pricelist'].sudo().search([('company_id','=',region.id)])
                    for pricelist in pricelists:
                        price = self.env.ref('base.USD')._convert(regionPrice.price,pricelist.currency_id,pricelist.company_id,date)
                        item_vals = {}
                        item_vals['product_tmpl_id'] = self.id
                        item_vals['pricelist_id'] = pricelist.id
                        item_vals['applied_on'] = '1_product'
                        item_vals['compute_price'] = 'fixed'
                        item_vals['fixed_price'] = price
                        item_vals['min_quantity'] = 1
                        item_vals['related_region_price_id'] = regionPrice.id

                        pricelist_item = self.env['product.pricelist.item'].search([('product_tmpl_id','=',self.id),('pricelist_id','=',pricelist.id)])
                        if not pricelist_item:
                            pricelist_item = self.env['product.pricelist.item'].sudo().create(item_vals)

                        else:
                            if regionPrice.override_default_price > 0:
                                item_vals['fixed_price'] = self.env.ref('base.USD')._convert(regionPrice.override_default_price,pricelist.currency_id,regionPrice.company_id,date)
                                pricelist_item.sudo().write(item_vals)

                            else:
                                pricelist_item.sudo().write({'fixed_price': item_vals['fixed_price']})
    
    @api.onchange('pack_ids')
    def _onchange_packs(self):
        if self.pack_ids:
            products = []
            for pack in self.pack_ids:
                products.append(pack.product_id.id)

            self.pack_product_ids = [(6, 0, products)]


    def show_related_registrations(self):
        res = {
        'type': 'ir.actions.act_window',
        'name': _('Product Registrations'),
        'view_mode': 'tree,form',
        'res_model': 'product.registration',
        'domain' : [('id','in',self.registration_ids.ids)],
        'target': 'current',
        'context': {'default_product_tmpl_id': self.id}
        }
        return res

    def compute_attempt(self):
        for record in self:
            record['passing_rate'] = 0
            record['train_to_test'] = 0
            record['avg_attempt'] = 0
            score = 0
            nb_attempt = 0
            attempted = 0
            attempts = record.registration_ids.mapped('attempt_ids')
            record['attempt_count'] = len(attempts)
            passed_attempts = attempts.filtered(lambda c: c.passing_status == 'passed')

            for registration in record.registration_ids:
                score += sum(registration.attempt_ids.mapped('score'))
                if registration.attempt_ids:
                    attempted += 1

            if attempted > 0:
                record['passing_rate'] = (len(passed_attempts) * 100) / attempted

            if record.registration_ids:
                record['train_to_test'] = attempted / len(record.registration_ids)

            record['avg_attempt'] = score / record.attempt_count if record.attempt_count > 0 else 0

    def _compute_cost_currency_id(self):
        for template in self:
            template.cost_currency_id = self.env.ref('base.USD').id
    


class Product(models.Model):
    _inherit = 'product.product'

    @api.onchange('session_ok')
    def _onchange_session_ok(self):
        """ Redirection, inheritance mechanism hides the method on the model """
        if self.session_ok:
            self.type = 'service'


    def action_open_quants(self):
        location_domain = self._get_domain_locations()[0]
        domain = expression.AND([[('product_id', 'in', self.ids)], location_domain])
        hide_location = not self.user_has_groups('stock.group_stock_multi_locations')
        hide_lot = all([product.tracking == 'none' for product in self])
        self = self.with_context(hide_location=hide_location, hide_lot=hide_lot)

        if self.user_has_groups('stock.group_stock_manager'):
            self = self.with_context(inventory_mode=True)
            if not self.user_has_groups('stock.group_stock_multi_locations'):
                user_company = self.env.company
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', user_company.id)], limit=1
                    )
                if warehouse:
                    self = self.with_context(default_location_id=warehouse.lot_stock_id.id)

        if len(self) == 1:
            self = self.with_context(
                default_product_id=self.id,
                single_product=True
            )
        else:
            self = self.with_context(product_tmpl_id=self.product_tmpl_id.id)

        ctx = dict(self.env.context)
        ctx.update({'no_at_date': True})
        ctx.update({'search_default_internal_loc': 1})
        return self.env['stock.quant'].with_context(ctx)._get_quants_action(domain)




    def _change_standard_price_company(self, new_price, company_id, counterpart_account_id=False):
        svl_vals_list = []
        for product in self:
            if product.cost_method not in ('standard', 'average'):
                continue

            quantity_svl = product.sudo().quantity_svl
            if float_is_zero(quantity_svl, precision_rounding=product.uom_id.rounding):
                continue

            diff = new_price - product.standard_price
            value = company_id.currency_id.round(quantity_svl * diff)
            if company_id.currency_id.is_zero(value):
                continue

            svl_vals = {
            'company_id': company_id.id,
            'product_id': product.id,
            'description': _('Product value manually modified (from %s to %s)') % (product.standard_price, new_price),
            'value': value,
            'quantity': 0,
            }
            svl_vals_list.append(svl_vals)

        stock_valuation_layers = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)
        product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}
        am_vals_list = []
        for stock_valuation_layer in stock_valuation_layers:
            product = stock_valuation_layer.product_id
            value = stock_valuation_layer.value

            if product.valuation != 'real_time':
                continue

            if counterpart_account_id is False:
                raise UserError(_('You must set a counterpart account.'))

            if not product_accounts[product.id].get('stock_valuation'):
                raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))

            if value < 0:
                debit_account_id = counterpart_account_id
                credit_account_id = product_accounts[product.id]['stock_valuation'].id

            else:
                debit_account_id = product_accounts[product.id]['stock_valuation'].id
                credit_account_id = counterpart_account_id

            move_vals = {
            'journal_id': product_accounts[product.id]['stock_journal'].id,
            'company_id': company_id.id,
            'ref': product.default_code,
            'stock_valuation_layer_ids': [(6, None, [stock_valuation_layer.id])],
            'line_ids': [(0, 0, {
                'name': _('%s changed cost from %s to %s - %s') % (self.env.user.name, product.standard_price, new_price, product.display_name),
                'account_id': debit_account_id,
                'debit': abs(value),
                'credit': 0,
                'product_id': product.id,
                }), (0, 0, {
                'name': _('%s changed cost from %s to %s - %s') % (self.env.user.name, product.standard_price, new_price, product.display_name),
                'account_id': credit_account_id,
                'debit': 0,
                'credit': abs(value),
                'product_id': product.id,
                })],
                }
            am_vals_list.append(move_vals)
        account_moves = self.env['account.move'].create(am_vals_list)
        account_moves.post()
        self.with_context(force_company=company_id.id).sudo().write({'standard_price': new_price})

