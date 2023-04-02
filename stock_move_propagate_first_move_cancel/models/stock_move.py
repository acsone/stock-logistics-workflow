# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _action_cancel(self):
        moves_to_cancel = self.search([("first_move_id", "in", self.ids)])
        return super(StockMove, moves_to_cancel | self)._action_cancel()
