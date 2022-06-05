# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, api, _


class InvoiceStockMove(models.Model):
    _inherit = 'account.move'

    def _get_stock_type_ids(self):
        data = self.env['stock.picking.type'].search([('company_id','=',self.company_id.id)])

        if self._context.get('default_type') == 'out_invoice':
            for line in data:
                if line.code == 'outgoing':
                    return line
        if self._context.get('default_type') == 'in_invoice':
            for line in data:
                if line.code == 'incoming':
                    return line

    def compute_picking_type(self):
        for record in self:
            record['picking_type_id'] = False
            warehouse = self.env['sale.order'].sudo().search([('name','=',record.invoice_origin),('name','!=','New')],limit=1).warehouse_id
            if not warehouse:
                warehouse = self.env['stock.warehouse'].sudo().search([('company_id','=',record.company_id.id)],limit=1)
            if warehouse:
                if record.move_type == 'out_invoice':
                    record['picking_type_id'] = warehouse.out_type_id.id

                elif record.move_type == 'out_refund':
                    record['picking_type_id'] = warehouse.in_type_id.id

    """def action_post(self):
        res = super(InvoiceStockMove, self).action_post()
        picking_type_id = False
        data = self.env['stock.picking.type'].search([('company_id','=',self.company_id.id)])
        if self._context.get('default_type') == 'out_invoice':
            for line in data:
                if line.code == 'outgoing':
                    picking_type_id = line.id
                    break

        if self._context.get('default_type') == 'in_invoice':
            for line in data:
                if line.code == 'incoming':
                    picking_type_id = line.id
                    break

        self.write({'picking_type_id': picking_type_id})

        return res"""

    """def action_post(self):
        res = super(InvoiceStockMove, self).action_post()
        if self.type == 'out_invoice':
            self.action_stock_move()
        
        elif self.type == 'out_refund':
            self.write({'invoice_picking_id': False})
            self.action_stock_move_refund()""

        
        return res"""

    def action_stock_move_refund(self):
        if not self.picking_type_id:
            raise UserError(_(" Please select a picking type"))

        for order in self:
            if not self.invoice_picking_id:
                pick = {}
                if self.picking_type_id.code == 'incoming':

                    destination = self.picking_type_id.default_location_dest_id.id
                    if self.picking_type_id.default_location_dest_id.location_id:
                        destination = self.picking_type_id.default_location_dest_id.location_id.id

                    pick = {
                    'picking_type_id': self.picking_type_id.id,
                    'partner_id': self.partner_id.id,
                    'origin': self.name,
                    'location_dest_id': destination,
                    'location_id': self.partner_id.property_stock_customer.id
                    }

                picking = self.env['stock.picking'].create(pick)
                self.invoice_picking_id = picking.id
                moves = order.invoice_line_ids.filtered(
                    lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)

                if moves:
                    move_ids = moves._action_confirm()
                    move_ids._action_assign()
                if not moves:
                    picking.unlink()

    picking_count = fields.Integer(string="Count", compute="_compute_picking",store=False)
    invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id")
    invoice_picking_ids = fields.One2many('stock.picking', 'account_move_id', string="Transfers")

    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type',
                                      compute="compute_picking_type",
                                      help="This will determine picking type of incoming shipment")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('posted', 'Posted'),
        ('post', 'Post'),
        ('cancel', 'Cancelled'),
        ('done', 'Received'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)

    def _compute_picking(self):
        for record in self:
            record['picking_count'] = len(record.sudo().invoice_picking_ids)

    def action_stock_move(self):
        if not self.picking_type_id:
            raise UserError(_(
                " Please select a picking type"))
        for order in self:
            if not self.invoice_picking_ids:
                pick = {}
                if self.picking_type_id.code == 'outgoing':
                    pick = {
                        'picking_type_id': self.picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'account_move_id': self.id,
                        'location_dest_id': self.partner_id.property_stock_customer.id,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                    }

                if self.picking_type_id.code == 'incoming':
                    pick = {
                        'picking_type_id': self.picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                        'location_id': self.partner_id.property_stock_supplier.id,
                        'account_move_id': self.id,
                    }
                picking = self.env['stock.picking'].create(pick)
                #self.invoice_picking_id = picking.id
                invoice_lines = order.invoice_line_ids.filtered(lambda r: r.product_id.type in ['product', 'consu'])
                invoice_lines += order.invoice_line_ids.filtered(lambda r: r.product_id.is_pack == True and r.product_id.type == 'service')
                moves = invoice_lines._create_stock_moves(picking)

                """products = order.invoice_line_ids.mapped('product_id')
                packs = products.mapped('pack_ids')
                packs = packs.filtered(lambda r: r.show_on_invoice == False)
                product_packs = packs.mapped('product_id')
                product_packs = product_packs.filtered(lambda r: r.type in ['product', 'consu'])
                pack_moves = self._create_stock_moves_products(picking,product_packs)"""
                
                #if moves:
                    #move_ids = moves._action_confirm()
                    #move_ids._action_assign()

                """pack_move_ids = pack_moves._action_confirm()
                pack_move_ids = pack_moves._action_assign()"""


    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('id', 'in', self.invoice_picking_ids.ids)]
        return result

    def _reverse_moves(self, default_values_list=None, cancel=False):
        ''' Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.

        :param default_values_list: A list of default values to consider per move.
                                    ('type' & 'reversed_entry_id' are computed in the method).
        :return:                    An account.move recordset, reverse of the current self.
        '''

        if self.picking_type_id.code == 'outgoing':
            data = self.env['stock.picking.type'].search([('company_id', '=', self.company_id.id),('code', '=', 'incoming')], limit=1)
            self.picking_type_id = data.id
        elif self.picking_type_id.code == 'incoming':
            data = self.env['stock.picking.type'].search([('company_id', '=', self.company_id.id),('code', '=', 'outgoing')], limit=1)
            self.picking_type_id = data.id
        reverse_moves = super(InvoiceStockMove, self)._reverse_moves()
        return reverse_moves


class SupplierInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move']
        product_qty = {}
        for line in self:
            if not line.product_id.is_pack:
                if line.product_id.id in product_qty:
                    product_qty[line.product_id.id] += line.quantity

                else:
                    product_qty[line.product_id.id] = line.quantity

            else:
                packs = line.product_id.mapped('pack_ids')
                product_packs = packs.mapped('product_id')
                product_packs = product_packs.filtered(lambda r: r.type in ['product', 'consu'])
                for pack in packs.filtered(lambda r: r.product_id.type in ['product', 'consu']):
                    quantity = line.quantity * pack.qty_uom
                    product_qty[pack.product_id.id] = quantity

        for line in self:
            price_unit = line.price_unit
            if not line.product_id.is_pack:
                if picking.picking_type_id.code =='outgoing':
                    template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': picking.picking_type_id.default_location_src_id.id,
                    'location_dest_id': line.move_id.partner_id.property_stock_customer.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.move_id.company_id.id,
                    'price_unit': price_unit,
                    'picking_type_id': picking.picking_type_id.id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                    'product_uom_qty': product_qty[line.product_id.id]
                    }

                if picking.picking_type_id.code == 'incoming':
                    template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': line.move_id.partner_id.property_stock_supplier.id,
                    'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.move_id.company_id.id,
                    'price_unit': price_unit,
                    'picking_type_id': picking.picking_type_id.id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                    'product_uom_qty': product_qty[product.id]
                    }
                    

                done += moves.create(template)

            else:
                if picking.picking_type_id.code == 'outgoing':
                    packs = line.product_id.sudo().mapped('pack_ids')
                    product_packs = packs.sudo().mapped('product_id')
                    product_packs = product_packs.filtered(lambda r: r.type in ['product', 'consu'])
                    for product in product_packs:
                        template = {
                        'name': product.display_name or '',
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'location_id': picking.picking_type_id.default_location_src_id.id,
                        'location_dest_id': line.move_id.partner_id.property_stock_customer.id,
                        'picking_id': picking.id,
                        'state': 'draft',
                        'company_id': line.move_id.company_id.id,
                        'picking_type_id': picking.picking_type_id.id,
                        'warehouse_id': picking.picking_type_id.warehouse_id.id,
                        'product_uom_qty': product_qty[product.id],
                        }

                        done += moves.sudo().create(template)

                if picking.picking_type_id.code == 'incoming':
                    for product in product_packs:
                        template = {
                        'name': product.display_name or '',
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'location_id': line.move_id.partner_id.property_stock_supplier.id,
                        'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                        'picking_id': picking.id,
                        'state': 'draft',
                        'company_id': line.move_id.company_id.id,
                        'picking_type_id': picking.picking_type_id.id,
                        'warehouse_id': picking.picking_type_id.warehouse_id.id,
                        'product_uom_qty': product_qty[product.id]
                        }

                        done += moves.sudo().create(template)
                        
        return done

