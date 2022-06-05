from odoo import models, fields
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    currency_id = fields.Many2one('res.currency', string="Currency")
    comment = fields.Char('Comment')
    region_id = fields.Many2one('res.company', string="Region")
    date_planned = fields.Date('Scheduled Date')
    is_region = fields.Boolean('Is Region')
    stage = fields.Selection(
        [('pending', 'Pending'),
        ('approved', 'Approved By Operartion'),
        ('cfo', 'CFO'),
        ('rejected', 'Rejected By Operation'),
        ('accountingapproved', 'Approved By accounting'),
        ('accountingreject', 'Rejected By Accounting')],
        string='Decision Maker')
    is_operation = fields.Boolean('Is Operation')
    timesheet_id = fields.Many2one('res.partner')
    name = fields.Char('Reference')
    order_date = fields.Date('Date Order')
    reason_for_rejection = fields.Text('Reason For Rejection')
    instructor_timesheets = fields.One2many('purchase.order', 'timesheet_id')
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('pendingbm', 'BM Approval'),
        ('pendingcm', 'CM Approval'),
        ('pendingacc', 'Accounting Approval'),
        ('pendingops', 'OPS action'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Order Placed'),
        ('received', 'Received'),
        ('done', 'Locked'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    company_id = fields.Many2one(
        'res.company',
        'Region',
        domain="[('is_region','=',True)]",
        required=True,
        index=True,
        default=lambda self: self._get_child_companies())


    def _get_child_companies(self):
        company = self.env.company
        child_company = self.env['res.company'].search([('parent_id','=',company.id)],limit=1)
        if child_company:
            return child_company.id
        
        else:
            return company.id


    def submit_order(self):
        self.ensure_one()
        date = self.date_order if self.date_order else datetime.now().strftime('%Y-%m-%d')
        rate = self.env['res.currency']._get_conversion_rate(self.env.ref('base.USD'),self.currency_id, self.company_id, date)
        order_lines = self.order_line.filtered(lambda line: line.product_id.is_pack == True and line.product_id.pack_ids != False)
        for line in order_lines:
            for pack in line.product_id.pack_ids.filtered(lambda p: p.product_id.type == 'product'):
                vals = {}
                supplier_info = self.env['product.supplierinfo'].search([('product_tmpl_id','=',pack.product_id.product_tmpl_id.id),('name','=',self.partner_id.id)],order="id desc",limit=1)
                vals['product_id'] = pack.product_id.id
                vals['order_id'] = self.id
                vals['name'] = pack.product_id.display_name
                vals['product_qty'] = pack.qty_uom * line.product_qty
                vals['product_uom'] = pack.product_id.uom_id.id
                vals['price_unit'] = supplier_info.price if supplier_info else pack.product_id.standard_price * rate
                vals['date_planned'] = fields.Date.today()
                vals['from_pack'] = True

                po_line = self.env['purchase.order.line'].sudo().search([('order_id','=',vals['order_id']),('product_id','=',vals['product_id'])])
                if not po_line:
                    po_line = self.env['purchase.order.line'].sudo().create(vals)

                else:
                    po_line.sudo().write(vals)

        order_lines = self.order_line.filtered(lambda line: line.product_id.is_pack == True and line.from_pack == False)
        order_lines.unlink()

        
        self.write({'state': 'pendingbm'})

    def export_purchase(self):
        doc_id = self.export_data(self)
        return {
        'type': 'ir.actions.act_url',
        'url':   '/web/content/' + str(doc_id) + '?download=true',
        'target': 'new',
        }

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    from_pack = fields.Boolean()

