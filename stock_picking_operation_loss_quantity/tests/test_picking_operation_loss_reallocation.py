# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from .common import OperationLossQuantityCommon


class TestPickingOperationLossNewReservation(OperationLossQuantityCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shelf_a = cls.env["stock.location"].create(
            {
                "name": "Shelf A",
                "usage": "internal",
                "location_id": cls.loc_stock.id,
            }
        )
        cls.shelf_b = cls.env["stock.location"].create(
            {
                "name": "Shelf B",
                "usage": "internal",
                "location_id": cls.loc_stock.id,
            }
        )
        cls._create_quantities(cls.product_2, 5.0, location=cls.shelf_a)
        cls._create_quantities(cls.product_2, 5.0, location=cls.shelf_b)

        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.pick_type_out.id,
                "location_id": cls.loc_stock.id,
                "location_dest_id": cls.loc_customer.id,
            }
        )
        cls.move = cls.env["stock.move"].create(
            {
                "picking_id": cls.picking.id,
                "name": "Test Fallback Move",
                "product_id": cls.product_2.id,
                "product_uom": cls.product_2.uom_id.id,
                "product_uom_qty": 5,
                "location_id": cls.loc_stock.id,
                "location_dest_id": cls.loc_customer.id,
            }
        )
        cls.move._action_confirm()
        cls.picking.action_assign()

    def test_loss_quantity_auto_reallocation(self):
        initial_line = self.move.move_line_ids[0]
        initial_reserved_location = initial_line.location_id
        fallback_location = (self.shelf_a | self.shelf_b) - initial_reserved_location

        initial_line.action_lose_quantity()

        self.assertNotIn(initial_line, self.move.move_line_ids)

        self.assertEqual(len(self.move.move_line_ids), 1)
        new_line = self.move.move_line_ids[0]

        self.assertEqual(new_line.location_id, fallback_location)
        self.assertEqual(new_line.reserved_uom_qty, 5.0)
