# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .stock_move import LOW_PRIORITY_VALUE


class StockPicking(models.Model):
    _inherit = "stock.picking"

    priority = fields.Selection(
        selection_add=[(LOW_PRIORITY_VALUE, "Not urgent"), ("0",)],
        ondelete={LOW_PRIORITY_VALUE: "set default"},
    )
