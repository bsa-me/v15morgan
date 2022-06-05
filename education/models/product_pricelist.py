from odoo import api, fields, models

class ProductPriceList(models.Model):
    _inherit = 'product.pricelist'

    product_tmpl_id = fields.Many2one('product.template','Product')
    is_region = fields.Boolean(related='company_id.is_region')
    company_id = fields.Many2one(required=False)
    website_id = fields.Many2one('website', string="Website", ondelete='restrict', domain=False)
    
    def _get_website_pricelists_domain(self, website_id):
        company_ids = self.sudo().search([('website_id','=',website_id)]).mapped('company_id').ids
        company_ids.append(False)
        return [
            '&', ('company_id', 'in', company_ids),('website_id','!=',False),
            '|', ('website_id', '=', website_id),
            '&', ('website_id', '=', False),
            '|', ('selectable', '=', True), ('code', '!=', False),
        ]

    def _is_available_on_website(self, website_id):
        self.ensure_one()
        if self.website_id.id == website_id:
          return True
        if self.company_id and self.company_id != self.env["website"].browse(website_id).company_id:
            return False
        return self.website_id.id == website_id or (not self.website_id and (self.selectable or self.sudo().code))

    @api.constrains('company_id', 'website_id')
    def _check_websites_in_company(self):
        for record in self.filtered(lambda pl: pl.website_id and pl.company_id):
            if record.website_id.company_id != record.company_id:
                return
    
    @api.model
    def create(self, vals):
      record = super(ProductPriceList, self).create(vals)
      record.currency_id.write({'companies_ids': record.currency_id.compute_companies()})
      return record

    def write(self, vals):
      record = super(ProductPriceList, self).write(vals)
      self.currency_id.write({'companies_ids': self.currency_id.compute_companies()})
      return super(ProductPriceList, self).write(vals)


    def _compute_price_event(self,event, ticket, currency):
      date = fields.Date.today()
      price = currency._convert(ticket.price, self.currency_id, event.company_id, date, round=False)
      item = self.env['product.pricelist.item'].search(['|',('date_end','>',date),('date_end','=',False),('pricelist_id','in',self.ids),('event_id','=',event.id),('applied_on','=','4_event')],order='id desc', limit=1)
      if item.compute_price == 'fixed':
        price = currency._convert(item.fixed_price, self.currency_id, event.company_id, date, round=False)

      elif item.compute_price == 'percentage':
        price = price - (price * item.percent_price/100)

      return price
        






