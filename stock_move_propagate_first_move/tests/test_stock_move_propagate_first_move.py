# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import Command

from .common import TestStockMovePickingTypeOrigin


class TestStockMovePropagateFirstMove(TestStockMovePickingTypeOrigin):
    def test_first_move_id_not_copied_during_split(self):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.loc_supplier.id,
                "location_dest_id": self.loc_in_1.id,
                "picking_type_id": self.picking_type_in.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 5,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.loc_supplier.id,
                            "location_dest_id": self.loc_in_1.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()

        picking.move_line_ids.qty_done = 2
        picking._action_done()

        backorder = picking.backorder_ids
        self.assertTrue(backorder, "No backorder picking was created")

        original_move = picking.move_ids
        backorder_move = backorder.move_ids
        self.assertNotEqual(
            backorder_move.first_move_id,
            original_move.first_move_id,
            "Backorder move should not keep the same first_move_id as the original move",
        )
