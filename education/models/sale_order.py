from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools import float_is_zero
from itertools import groupby
from datetime import datetime
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    order_line = fields.One2many(
        'sale.order.line',
        'order_id',
        string='Order Lines',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)], 'locked': [('readonly', True)], 'sale': [('readonly', True)]},
        copy=True,
        auto_join=True)
    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', check_company=True,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        states={'locked': [('readonly', True)], 'sale': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('locked', 'Locked'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Finalized'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    company_id = fields.Many2one(
        'res.company',
        'Region',
        domain="[('is_region','=',True)]",
        required=True,
        index=True,
        default=lambda self: self._get_child_companies(),
        states={'locked': [('readonly', True)], 'sale': [('readonly', True)]})


    partner_id = fields.Many2one(
        'res.partner', string='Account', readonly=True,
        states={'draft': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    registration_ids = fields.One2many('event.registration', 'sale_order_id', 
                                        string='Attendees', readonly=True) 
    event_ids = fields.Many2many('event.event', string='Event', 
                                 compute='_compute_event_ids', 
                                 readonly=True)

    product_ids = fields.Many2many('product.product',string='Products',store=True)

    amount_discount = fields.Float(string='Total Discount',compute="get_amount_discount")

    event_id = fields.Many2one('event.event')

    product_filter_ids = fields.Char('Product ids',compute="compute_filters", store=True)
    event_filter_ids = fields.Char('Event ids',compute="compute_filters",store=True)
    mrm_lifecycle_status = fields.Char('MRM Status')
    mrm_name = fields.Char('MRM Name')
    other_inv_ref = fields.Char()
    mrm = fields.Boolean("From MRM")
    invoice_created = fields.Boolean()

    @api.depends('order_line')
    def compute_filters(self):
        for record in self:
            products = str(self.order_line.mapped('product_id').ids)
            products = products.replace("[", "")
            products = products.replace("]", "")
            products = products.replace(" ", "")

            events = str(self.order_line.mapped('event_id').ids)
            events = events.replace("[", "")
            events = events.replace("]", "")
            events = events.replace(" ", "")

            record['product_filter_ids'] = products
            record['event_filter_ids'] = events

    
    @api.model
    def create(self, vals):
        if "website_id" in vals and "pricelist_id" in vals:
            company_id = self.env['product.pricelist'].sudo().browse(vals['pricelist_id']).company_id.id
            warehouse = self.env['stock.warehouse'].sudo().search([('company_id','=',company_id)],limit=1)
            vals['company_id'] = company_id
            vals['warehouse_id'] = warehouse.id
        record = super(SaleOrder, self).create(vals)
        if record.opportunity_id:
            """if(record.state not in ['sale','done']):
                opportunity = record.opportunity_id
                if(opportunity.stage_id != self.env.ref('crm.stage_lead4')):
                    self.env.cr.execute("UPDATE crm_lead set stage_id = " + str(self.env.ref('crm.stage_lead3').id) + " where id = " + str(opportunity.id))"""

            total_revenue = self.amount_total

            orders = self.search([('opportunity_id','=',record.opportunity_id.id),('id','!=',record.id)])
            if orders:
                for order in orders:
                    total_revenue += order.amount_total

            #self.env.cr.execute("UPDATE crm_lead set planned_revenue = " + str(total_revenue) + " where id = " + str(record.opportunity_id.id))
            #record.opportunity_id.write({'planned_revenue': total_revenue})

        if not record.website_id:
            name = False
            if(record.state=='draft'):
                name = 'New'

            if(record.state!='draft' and record.name=='New'):
                code = 'sale.order'
                ref = 'SO'
                company_sequence = False
                parent_sequence = False

                if(not record.company_id.document_sequence):
                    company_sequence = self.env['ir.sequence'].search([('company_id','=',record.company_id.id),('code','=',code),('prefix','=','SO')],limit=1)
                    name = ref + '-' + record.company_id.code + '-' + str(company_sequence.number)
                    company_sequence.write({'number': company_sequence.number + 1})

                else:
                    parent_sequence = self.env['ir.sequence'].search([('company_id','=',record.company_id.parent_id.id),('code','=',code),('prefix','=','SO')],limit=1)
                    if(parent_sequence):
                        name = ref + '-' + record.company_id.parent_id.code + '-' + str(parent_sequence.number)
                        parent_sequence.write({'number': parent_sequence.number + 1})

            record['name'] = name

        return record

    def write(self, vals):

        if self.opportunity_id:

            date = datetime.now().strftime('%Y-%m-%d')
            if 'order_line' in vals:
                self._amount_all()

            total_revenue = self.currency_id._convert(self.amount_total,self.opportunity_id.company_currency,self.company_id,date)

            orders = self.search([('opportunity_id','=',self.opportunity_id.id),('id','!=',self.id)])
            if orders:
                for order in orders:
                    amount = order.currency_id._convert(order.amount_total,order.opportunity_id.company_currency,order.company_id,date)
                    total_revenue += amount

            #self.env.cr.execute("UPDATE crm_lead set planned_revenue = " + str(total_revenue) + " where id = " + str(self.opportunity_id.id))
            self.env.cr.execute("UPDATE crm_lead set quotation_revenue = " + str(total_revenue) + " where id = " + str(self.opportunity_id.id))
        
        return super(SaleOrder, self).write(vals)
    def action_lock(self):

        code = 'sale.order'
        ref = 'SO'
        name = False
        company_sequence = False
        parent_sequence = False

        if not self.website_id and 'SO-' not in self.name:
            if(not self.company_id.document_sequence):
                company_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.id),('code','=',code),('prefix','=','SO')],limit=1)
                name = ref + '-' + self.company_id.code + '-' + str(company_sequence.number)
                company_sequence.write({'number': company_sequence.number + 1})

                self.write({'name': name})

            else:
                parent_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.parent_id.id),('code','=',code),('prefix','=','SO')],limit=1)
                if(parent_sequence):
                    name = ref + '-' + self.company_id.parent_id.code + '-' + str(parent_sequence.number)
                    parent_sequence.write({'number': parent_sequence.number + 1})

                self.write({'name': name})

        expiry = datetime.today() + timedelta(days=10)
        self.write({'state': 'locked', 'validity_date': expiry})
    
    def action_unlock(self):
        self.write({'state': 'draft'})

        
    def action_confirm(self):
        for so in self:
            if any(so.order_line.filtered(lambda line: line.event_id)):
                return self.env['ir.actions.act_window'] \
                    .with_context(default_sale_order_id=so.id) \
                    ._for_xml_id('education.action_sale_order_full_registration')
                
                    
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])

        if self.opportunity_id and self.amount_total > 0:
            self.opportunity_id.action_set_won_rainbowman()

        for line in self.order_line:
            if not line.event_id:
                template = line.product_id.product_tmpl_id
                registration = self.env['product.registration'].search([('partner_id','=',self.partner_id.id),('product_tmpl_id','=',template.id)])
                if not registration:
                    registration = self.env['product.registration'].create({
                        'partner_id': self.partner_id.id,
                        'product_tmpl_id': template.id,
                        'date_open': self.date_order,
                        'sale_order_id': self.id,
                        'origin': self.name,
                        'sale_order_line_id': line.id,
                        'company_id': self.company_id.id,
                        })

                registration.onchange_partner_id()

        for line in self.order_line.filtered(lambda r: r.product_id.product_tmpl_id.is_pack == True and r.is_reward_line == True):
            template = line.product_id.product_tmpl_id
            if template.pack_ids:
                for pack in template.pack_ids:
                    vals = {}
                    vals['product_id'] = pack.product_id.id
                    vals['product_uom'] = pack.product_id.uom_id.id
                    vals['order_id'] = self.id
                    vals['product_uom_qty'] = line.product_uom_qty * pack.qty_uom
                    vals['name'] = pack.product_id.display_name
                    vals['is_reward_line'] = line.is_reward_line
                    vals['discount'] = line.discount
                    vals['tax_id'] = [(6, 0, line.tax_id.ids)]
                    order_line = self.env['sale.order.line'].search([('product_id','=',vals['product_id']),('order_id','=',vals['order_id']),('discount','=',vals['discount'])])
                    if order_line:
                        order_line.write(vals)

                    else:
                        if vals['is_reward_line'] == True:
                            vals['name'] = line.name

                        order_line = self.env['sale.order.line'].create(vals)
        self.order_line.filtered(lambda r: r.product_id.product_tmpl_id.is_pack == True and r.is_reward_line == True).unlink()


        self.write({
            'state': 'sale',
            'date_order': fields.Datetime.now()
        })

        self._action_confirm()

                
    def _action_confirm(self):
        for so in self:
            # confirm registration if it was free (otherwise it will be confirmed once invoice fully paid)
            so.order_line._update_registrations(confirm=so.amount_total == 0, cancel_to_draft=False)

            receivable_account = so.partner_id.property_account_receivable_id
            receivable = self.env['account.account'].search([('code','=',receivable_account.code),('company_id','=',so.company_id.id),('user_type_id','=',receivable_account.user_type_id.id)],limit=1)

            payable_account = so.partner_id.property_account_payable_id
            payable = self.env['account.account'].search([('code','=',payable_account.code),('company_id','=',so.company_id.id),('user_type_id','=',payable_account.user_type_id.id)],limit=1)

            so.partner_id.write({'property_account_receivable_id': receivable.id, 'property_account_payable_id': payable.id})

            for line in so.order_line:
                income_account = self.env['account.account'].search([('code','=','400000'),('company_id','=',so.company_id.id)],limit=1)
                line.product_id.write({'property_account_income_id': income_account.id})

        return super(SaleOrder, self)._action_confirm()

    def action_confirm_order(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
                ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])

        if self.opportunity_id and self.amount_total > 0:
            self.opportunity_id.action_set_won_rainbowman()

        self.write({
            'state': 'sale',
            'date_order': fields.Datetime.now()

        })
        self._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()

        return True
        
    @api.depends('order_line.event_id')
    def _compute_event_ids(self):
        for sale in self:
            sale.event_ids = sale.order_line.event_id
            
    def _session_seats_available(self):
        tracks = {}
        for line in self.mapped('order_line').filtered(lambda x: 
            x.event_track_seats_availability == 'limited'):
            tracks.setdefault(line.track_id,line.event_track_seats_available)
            tracks[line.track_id] -= line.product_uom_qty
            if tracks[line.track_id] < 0:
                return False
            return True
            
    def action_cancel(self):
        for line in self.order_line:
            if line.event_id:
                #raise UserError(self.env['event.registration'].search([('event_id','=',line.event_id.id),('sale_order_id','=',self.id)]))
                self.env['event.registration'].search([('event_id','=',line.event_id.id),('sale_order_id','=',self.id)]).button_reg_cancel()

            if line.session_id:
                self.env['event.registration'].search([('event_id','=',line.event_id.id),('sale_order_id','=',self.id)]).button_reg_cancel()


        return self.write({'state': 'cancel'})

    def get_amount_discount(self):
        for record in self:
            record.amount_discount = 0
            discount = 0
            reward_lines = record.order_line.filtered(lambda o: o.is_reward_line)
            discount += -sum(reward_lines.mapped('price_subtotal'))
            discount_ids = record.order_line.filtered(lambda o: o.discount_ids != False)
            for line in discount_ids:
                discount += line.price_unit * line.product_uom_qty - line.price_subtotal

            record.amount_discount = discount

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and not self.website_id:
            self.pricelist_id = False

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id and not self.website_id:
            self.pricelist_id = False
            warehouse = self.env['stock.warehouse'].search([('company_id','=',self.company_id.id)],limit=1)
            if warehouse:
                self.warehouse_id = warehouse.id


    @api.onchange('pricelist_id')
    def onchange_pricelist(self):
        if self.pricelist_id:
            event_regist = self.env.ref('event_sale.product_product_event').id
            session_regist = self.env.ref('education.product_product_session').id
            products = []
            products.append(event_regist)
            products.append(session_regist)
            if self.pricelist_id.item_ids:
                for line in self.pricelist_id.item_ids:
                    if line.product_tmpl_id:
                        if line.product_tmpl_id.product_variant_id:
                            products.append(line.product_tmpl_id.product_variant_id.id)
            #raise UserError(products)
            if products:
                self.product_ids = [(6, 0, products)]

    def _prepare_invoice(self):
        self.ensure_one()
        journal = self.env['account.move'].with_context(force_company=self.company_id.id, default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        invoice_vals = {
        'ref': self.client_order_ref or '',
        'move_type': 'out_invoice',
        'narration': self.note,
        'currency_id': self.pricelist_id.currency_id.id,
        'campaign_id': self.campaign_id.id,
        'medium_id': self.medium_id.id,
        'source_id': self.source_id.id,
        'invoice_user_id': self.user_id and self.user_id.id,
        'team_id': self.team_id.id,
        'partner_id': self.partner_id.id,
        'partner_shipping_id': self.partner_shipping_id.id,
        #'invoice_partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
        'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
        'invoice_origin': self.name,
        'invoice_payment_term_id': self.payment_term_id.id,
        #'invoice_payment_ref': self.reference,
        'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        'invoice_line_ids': [],
        'company_id': self.company_id.id,
        }

        return invoice_vals

    def _get_child_companies(self):
        company = self.env.company
        child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
        if child_company:
            return child_company.id

        else:
            return company.id




    """@api.onchange('opportunity_id')
    def onchange_opportuntiy_id(self):
        if self.opportunity_id.event_id:
            order_lines = []
            event = self.opportunity_id.event_id
            order_lines.append((0, 0, {'name': event.name, 'price_unit': 0, 'event_id': event.id, 'product_id': self.env.ref('event_sale.product_product_event_product_template').id, 'product_uom_qty': 1, 'product_uom': self.env.ref('uom.product_uom_unit').id}))
            self['order_line'] = order_lines

        if self.opportunity_id.partner_id:
            self.partner_id = self.opportunity_id.partner_id.id"""

    def recompute_coupon_lines(self):
        for order in self:
            order._remove_reward_lines()
            order._apply_bundle_promotions()
            order._create_new_no_code_promo_reward_lines()
            #order._update_existing_reward_lines()

    def _remove_reward_lines(self):
        self.ensure_one()
        order = self
        order_lines = self.env['sale.order.line'].search([('order_id','in',order.ids),('order_id.promo_code','=',False),('is_reward_line','=',1)]).unlink()

    def _apply_bundle_promotions(self):
        self.ensure_one()
        order = self
        bundle = False
        qty = 1
        product_ids = self.order_line.mapped('product_id').ids
        templates = self.env['product.template'].search([('pack_product_ids','=',product_ids)])
        for template in templates:
            if len(template.pack_product_ids) == len(product_ids):
                self.env['sale.order.line'].search([('product_id','in',product_ids),('order_id','in',self.ids)],limit=1).product_uom_qty
                self.env['sale.order.line'].search([('product_id','in',product_ids),('order_id','in',self.ids)]).unlink()
                bundle = template
                break
        if bundle:
            bundle_order_line = self.env['sale.order.line'].search([('order_id','=',self.id),('product_id','=',bundle.id)])
            if not bundle_order_line:
                bundle_order_line = self.env['sale.order.line'].create({
                    'product_id': bundle.product_variant_id.id,
                    'order_id': self.id,
                    'product_uom': bundle.uom_id.id,
                    'product_uom_qty': qty,
                    })

            bundle_order_line.product_id_change()




    def _create_invoices(self, grouped=False, final=False):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            
            except AccessError:
                return self.env['account.move']

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoice_vals_list = []
        for order in self:
            pending_section = None
            invoice_vals = order._prepare_invoice()
            if order.website_id:
                order.write({'state': 'sale'})
                for line in order.order_line:
                    line.write({'qty_to_invoice': line.product_uom_qty})
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue

                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None

                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered. '  + self.name))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        if not grouped:
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('partner_id'), x.get('currency_id'))):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']

                    origins.add(invoice_vals['invoice_origin'])
                    #payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])

                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    #'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                    })

                new_invoice_vals_list.append(ref_invoice_vals)

            invoice_vals_list = new_invoice_vals_list

        #raise UserError(str(invoice_vals_list))
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()

        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
                )
        return moves

    def _get_reward_values_product(self, program):
        price_unit = self.pricelist_id.get_product_price(program.reward_product_id, 1, self.partner_id, date=False, uom_id=False)
        order_lines = (self.order_line - self._get_reward_lines()).filtered(lambda x: program._is_valid_product(x.product_id))
        max_product_qty = sum(order_lines.mapped('product_uom_qty')) or 1
        if program._is_valid_product(program.reward_product_id):
            program_in_order = max_product_qty // (program.rule_min_quantity + program.reward_product_quantity)
            reward_product_qty = program.reward_product_quantity * program_in_order

        else:
            reward_product_qty = min(max_product_qty, self.order_line.filtered(lambda x: x.product_id == program.reward_product_id).product_uom_qty)

        reward_qty = min(int(int(max_product_qty / program.rule_min_quantity) * program.reward_product_quantity), reward_product_qty)
        taxes = program.reward_product_id.taxes_id
        if self.fiscal_position_id:
            taxes = self.fiscal_position_id.map_tax(taxes)

        

        return {
        'product_id': program.reward_product_id.id,
        'price_unit': price_unit,
        'product_uom_qty': program.reward_product_quantity,
        'discount': 100,
        'is_reward_line': True,
        'name': _("Free Product") + " - " + program.reward_product_id.name,
        'product_uom': program.reward_product_id.uom_id.id,
        #'tax_id': [(4, tax.id, False) for tax in taxes],
        }

    def _create_new_no_code_promo_reward_lines(self):
        self.ensure_one()
        order = self
        programs = order._get_applicable_no_code_promo_program()
        programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs:
            error_status = program._check_promo_code(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    order._create_reward_coupon(program)
                
                elif program.discount_line_product_id.id not in self.order_line.mapped('product_id').ids:
                    values = self._get_reward_line_values(program)

                    if program.discount_apply_on == 'specific_events':
                        if program.discount_type == 'percentage':
                            if program.applied_on == 'tuition':
                                lines = self.order_line.filtered(lambda l: l.event_id.course_id.id in program.course_ids.ids)
                                total = sum([l.price_subtotal for l in lines if l.event_ticket_id])
                                price_unit = -total * program.discount_percentage / 100
                                updated_price_unit = {"price_unit": price_unit}
                                for value in values:
                                    price_unit = total
                                    value.update(updated_price_unit)

                            elif program.applied_on == 'mappeditems':
                                mapped_items = self.order_line.mapped('event_ticket_id').filtered(lambda ticket: ticket.event_id.course_id.id in program.course_ids.ids).mapped('mapped_item_ids').mapped('product_variant_ids')
                                total = sum([l.price_subtotal for l in self.order_line if l.product_id in mapped_items])
                                price_unit = -total * program.discount_percentage / 100
                                updated_price_unit = {"price_unit": price_unit}
                                for value in values:
                                    price_unit = total
                                    value.update(updated_price_unit)

                    for value in values:
                        if 'On product with following tax' not in value['name']:
                            if value['product_id'] not in self.order_line.mapped('product_id').ids:
                                self.write({'order_line': [(0, False, value)]})

                order.no_code_promo_program_ids |= program



    def _create_delivery_line(self, carrier, price_unit):
        res = super(SaleOrder, self)._create_delivery_line(carrier, price_unit)
        #res.write({'is_delivery': False})
        return res

    def _get_reward_values_discount(self, program):
        if program.discount_type == 'fixed_amount':
            return [{
            'name': _("Discount: ") + program.name,
            'product_id': program.discount_line_product_id.id,
            'price_unit': - self._get_reward_values_discount_fixed_amount(program),
            'product_uom_qty': 1.0,
            'product_uom': program.discount_line_product_id.uom_id.id,
            'is_reward_line': True,
            'tax_id': [(4, tax.id, False) for tax in program.discount_line_product_id.taxes_id],
            }]

        reward_dict = {}
        lines = self._get_paid_order_lines()
        if program.discount_apply_on == 'cheapest_product':
            line = self._get_cheapest_line()
            if line:
                discount_line_amount = line.price_reduce * (program.discount_percentage / 100)
                if discount_line_amount:
                    taxes = line.tax_id
                    if self.fiscal_position_id:
                        taxes = self.fiscal_position_id.map_tax(taxes)

                    reward_dict[line.tax_id] = {
                    'name': _("Discount: ") + program.name,
                    'product_id': program.discount_line_product_id.id,
                    'price_unit': - discount_line_amount,
                    'product_uom_qty': 1.0,
                    'product_uom': program.discount_line_product_id.uom_id.id,
                    'is_reward_line': True,
                    'tax_id': [(4, tax.id, False) for tax in taxes],
                    }

        elif program.discount_apply_on in ['specific_products', 'specific_events', 'on_order']:
            if program.discount_apply_on == 'specific_products':
                free_product_lines = self.env['coupon.program'].search([('reward_type', '=', 'product'), ('reward_product_id', 'in', program.discount_specific_product_ids.ids)]).mapped('discount_line_product_id')
                lines = lines.filtered(lambda x: x.product_id in (program.discount_specific_product_ids | free_product_lines))

            for line in lines:
                discount_line_amount = self._get_reward_values_discount_percentage_per_line(program, line)

                if discount_line_amount:
                    if line.tax_id in reward_dict:
                        reward_dict[line.tax_id]['price_unit'] -= discount_line_amount

                    else:
                        taxes = line.tax_id
                        if self.fiscal_position_id:
                            taxes = self.fiscal_position_id.map_tax(taxes)

                        """tax_name = ""
                        if len(taxes) == 1:
                            tax_name = " - " + _("On product with following tax: ") + ', '.join(taxes.mapped('name'))

                        elif len(taxes) > 1:
                            tax_name = " - " + _("On product with following taxes: ") + ', '.join(taxes.mapped('name'))"""

                        taxes = False
                        if program.discount_line_product_id.taxes_id:
                            taxes = program.discount_line_product_id.taxes_id.filtered(lambda t: t.id in self.company_id.tax_ids.ids)
                            if taxes:
                                taxes = [(6, 0, taxes.ids)]
                                

                        reward_dict[line.tax_id] = {
                        'name': _("Discount: ") + program.name,
                        'product_id': program.discount_line_product_id.id,
                        'price_unit': - discount_line_amount,
                        'product_uom_qty': 1.0,
                        'product_uom': program.discount_line_product_id.uom_id.id,
                        'is_reward_line': True,
                        'tax_id': taxes
                        }

        max_amount = program._compute_program_amount('discount_max_amount', self.currency_id)
        if max_amount > 0:
            amount_already_given = 0
            for val in list(reward_dict):
                amount_to_discount = amount_already_given + reward_dict[val]["price_unit"]
                if abs(amount_to_discount) > max_amount:
                    reward_dict[val]["price_unit"] = - (max_amount - abs(amount_already_given))
                    add_name = formatLang(self.env, max_amount, currency_obj=self.currency_id)
                    reward_dict[val]["name"] += "( " + _("limited to ") + add_name + ")"

                amount_already_given += reward_dict[val]["price_unit"]
                if reward_dict[val]["price_unit"] == 0:
                    del reward_dict[val]

        return reward_dict.values()