from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    deliverable_rate = fields.Float(
        compute="_compute_deliverable_rate",
        search="_search_deliverable_rate",
        digits="Sale order deliverable rate",
        store=False,
    )

    def _compute_deliverable_rate(self):
        for rec in self:
            # filter order_lines who still need to be satisfies and count it
            nb_order_line = len(
                rec.order_line.filtered(lambda line: line.qty_to_ship > 0)
            )
            # if order_lines still need to be satisfies
            # we make avg of their deliverable_rate
            if nb_order_line > 0:
                rec.deliverable_rate = (
                    sum(rec.order_line.mapped("deliverable_rate")) / nb_order_line
                )
            else:
                rec.deliverable_rate = 100

    def _search_deliverable_rate(self, operator, value):
        lines = self.env["sale.order.line"].search([("qty_to_ship", ">=", 0)])

        orders = lines.mapped("order_id")

        orders = orders.filtered_domain([("deliverable_rate", operator, value)])

        return [("id", "in", orders.ids)]
