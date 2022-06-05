from odoo import fields, models, api

class Picking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(Picking, self).action_done()
        if self.move_line_ids:
            for line in self.move_line_ids:
                line._compute_qty_done()

        return res

