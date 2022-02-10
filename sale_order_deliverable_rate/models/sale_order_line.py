from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_to_ship = fields.Integer(compute="_compute_qty_to_ship", store=True)
    deliverable_rate = fields.Integer(compute="_compute_deliverable_rate", store=False)

    @api.depends("product_uom_qty", "qty_delivered")
    def _compute_qty_to_ship(self):
        for rec in self:
            rec.qty_to_ship = rec.product_uom_qty - rec.qty_delivered

    @api.depends("product_id", "qty_delivered", "qty_to_ship")
    def _compute_deliverable_rate(self):
        for rec in self:
            if rec.qty_to_ship > 0:
                rate = rec.product_id.qty_available / rec.qty_to_ship
                rec.deliverable_rate = min(100, rate * 100)
            else:
                rec.deliverable_rate = 0
