from odoo import models, fields
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    mrm_lifecycle_status = fields.Char('MRM Status')
    mrm_name = fields.Char('MRM Name')
    other_inv_ref = fields.Char()
    mrm = fields.Boolean("From MRM")
    invoice_created = fields.Boolean()

    def fix_negative_quotations(self):
        orders = self.env['sale.order'].search([('mrm','=',True),('state','=','sale'),('amount_total','<',0)])
        for order in orders:
            for line in order.order_line:
                line.write({'price_unit': -line.price_unit})
                line._compute_amount()

            order._amount_all()


    def create_mrm_invoices(self):
        inv_orders = self.env['sale.order'].sudo().search([('mrm','=',True),('state','=','sale'),('name','ilike','SO SI'),('invoice_created','=',False),('order_line','!=',False)],limit=1000)
        #raise UserError(inv_orders.mapped('company_id').mapped('name'))
        for order in inv_orders:
            inv_moves = order._create_invoices(final=True)
            invoice_name = inv_moves.invoice_origin.split(' ')[1]
            invoice_name = "'" + invoice_name + "'"

            self.env.cr.execute("update account_move set name = " + invoice_name + " where id = " + str(inv_moves.id))
            #inv_moves.write({'name': invoice_name})
            order.write({'invoice_created': True})
            #inv_moves.action_post()

    def create_mrm_credit_notes(self):
        cr_orders = self.env['sale.order'].search([('mrm','=',True),('state','=','sale'),('name','ilike','SO CR'),('invoice_created','=',False),('order_line','!=',False)],limit=500)
        for order in cr_orders:
            order_lines = self.env['sale.order.line'].search([('order_id','=',order.id)]).write({'qty_invoiced': 0})

            refund_moves = order._create_invoices(final=True)
            self.env.cr.execute("update account_move set type ='out_refund' where id = " + str(refund_moves.id))
            try:
                move_name = 'SI' + order.other_inv_ref.split(' ')[1]
                origin_invoice = self.env['account.move'].search([('name','=',move_name)],limit=1)
                if origin_invoice:
                    #refund_moves.write({'reversed_entry_id': origin_invoice.id})
                    self.env.cr.execute("update account_move set reversed_entry_id = " + str(origin_invoice.id) + " where id = " + str(refund_moves.id))
            except:
                print('')

            credit_note_name = refund_moves.invoice_origin.split(' ')[1]
            credit_note_name = "'" + credit_note_name + "'"
            #refund_moves.write({'name': credit_note_name})
            self.env.cr.execute("update account_move set name = " + credit_note_name + " where id = " + str(refund_moves.id))
            order.write({'invoice_created': True})
            #refund_moves.action_post()
            



    def link_sales_to_registrations(self):
        inv_orders = self.env['sale.order'].search([('mrm','=',True),('state','=','sale'),('name','ilike','SO SI')])
        for order in inv_orders:
            for line in order.order_line.filtered(lambda l: l.event_id != False):
                registration = self.env['event.registration'].search([('sale_order_id','=',order.id),('sale_order_line_id','=',line.id),('event_id','=',line.event_id.id),('partner_id','=',order.partner_id.id)])

                if not registration:
                    registration = self.env['event.registration'].create({
                        'partner_id': order.partner_id.id,
                        'event_id': line.event_id.id,
                        'sale_order_id': order.id,
                        'sale_order_line_id': line.id,
                        })
                    
                
                registration.write({'date_open': order.date_order})
                registration._onchange_partner()
                registration.confirm_registration()

        refund_orders = self.env['sale.order'].search([('mrm','=',True),('state','=','sale'),('name','ilike','SO CR')])
        for order in refund_orders:
            for line in order.order_line.filtered(lambda l: l.event_id != False):
                registration = self.env['event.registration'].search([('sale_order_id','=',order.id),('sale_order_line_id','=',line.id),('event_id','=',line.event_id.id),('partner_id','=',order.partner_id.id)])

                if not registration:
                    registration = self.env['event.registration'].create({
                        'partner_id': order.partner_id.id,
                        'event_id': line.event_id.id,
                        'sale_order_id': order.id,
                        'sale_order_line_id': line.id,
                        })
                
                registration.write({'transfer_status': 'dropout'})
                registration._onchange_partner()
                registration.button_reg_cancel()





