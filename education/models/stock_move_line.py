from odoo import fields, models, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    qty_done_sign = fields.Float(string="Qty Done",compute="_compute_qty_done",store=True)
    qty_demand = fields.Float(related="move_id.product_uom_qty")
    source_document = fields.Char('Source Document',compute="_compute_info")
    from_company = fields.Char('From',compute="_compute_info")
    from_partner_id = fields.Many2one('res.partner',compute="_compute_info",string='From')
    to_partner_id = fields.Many2one('res.partner',compute="_compute_info",string='To')
    note = fields.Text('Notes')
    
    @api.depends('picking_code', 'location_id', 'location_dest_id')
    def _compute_qty_done(self):
        for record in self:
            record['qty_done_sign'] = 0
            if record.picking_code == 'incoming':
                record['qty_done_sign'] = record.qty_done

            elif record.picking_code == 'outgoing':
                record['qty_done_sign'] = -record.qty_done

            elif record.location_id.usage == 'internal' and record.location_dest_id.usage != 'internal':
                record['qty_done_sign'] = -record.qty_done

            elif record.location_id.usage != 'internal' and record.location_dest_id.usage == 'internal':
                record['qty_done_sign'] = record.qty_done

            elif record.location_id.usage == 'internal' and record.location_dest_id.usage == 'internal':
                record['qty_done_sign'] = record.qty_done


    def _compute_info(self):
        for record in self:
            record['source_document'] = ''
            record['from_partner_id'] = False
            record['to_partner_id'] = False
            if record.reference:
                picking = self.env['stock.picking'].sudo().search([('name','=',record.reference)],limit=1)
                if picking:
                    record['source_document'] = picking.sudo().origin

            if record.location_id.usage == 'internal':
                record['from_partner_id'] = record.location_id.company_id.partner_id.id

            elif record.location_id.usage == 'customer' or record.location_id.usage == 'supplier':
                picking = self.env['stock.picking'].search([('name','=',record.reference)],limit=1)
                if picking:
                    record['from_partner_id'] = picking.partner_id.id
                    

            
            if record.location_dest_id.usage == 'internal':
                record['to_partner_id'] = record.location_dest_id.company_id.partner_id.id

            elif record.location_dest_id.usage == 'customer' or record.location_dest_id.usage == 'supplier':
                picking = self.env['stock.picking'].search([('name','=',record.reference)],limit=1)
                if picking:
                    record['to_partner_id'] = picking.partner_id.id





