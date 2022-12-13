# Author: Jacques-Etienne Baudoux <je@bcim.be>
# Copyright (C) 2015-2022 BCIM <http://www.bcim.be>
#                         ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    count_picking_grn = fields.Integer(compute="_compute_count_picking_grn")

    def _compute_count_picking_grn(self):
        data = self.env["stock.picking"]._read_group(
            [
                ("grn_id", "!=", False),
                ("state", "not in", ("done", "cancel")),
                ("picking_type_id", "in", self.ids),
            ],
            ["picking_type_id"],
            ["picking_type_id"],
        )
        count = {
            x["picking_type_id"][0]: x["picking_type_id_count"]
            for x in data
            if x["picking_type_id"]
        }
        for rec in self:
            rec.count_picking_grn = count.get(rec.id, 0)

    def get_action_picking_tree_grn(self):
        return self._get_action("stock_grn.action_picking_tree_grn")
