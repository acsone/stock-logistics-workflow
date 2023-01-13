# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    assignation_max_weight = fields.Float(
        compute="_compute_assignation_max_weight",
        digits="Stock Weight",
        store=True,
        help="Technical field that represent the maximum weight for a move that"
        "is acceptable for this picking assignation",
    )

    @api.depends("picking_type_id.group_pickings_maxweight", "weight")
    def _compute_assignation_max_weight(self):
        for picking in self:
            picking.assignation_max_weight = (
                picking.picking_type_id.group_pickings_maxweight - picking.weight
            )

    @api.model
    def _get_index_for_grouping_fields(self):
        """
        This tuple is intended to be overriden in order to add fields
        used in groupings
        """
        res = super()._get_index_for_grouping_fields()
        if "assignation_max_weight" not in res:
            res.append("assignation_max_weight")
        return res

    def init(self):
        """
        This has to be called in every overriding module
        """
        self._create_index_for_grouping()
