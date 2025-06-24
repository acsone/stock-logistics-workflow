# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestPickingDestinationSuggest(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.warehouse.delivery_steps = "pick_ship"

        cls.customers = cls.env.ref("stock.stock_location_customers")
        cls.customer = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.group = cls.env["procurement.group"].create(
            {
                "name": "Partner_test",
                "partner_id": cls.customer.id,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )
        cls.product.route_ids |= cls.warehouse.delivery_route_id
        cls.output = cls.env.ref("stock.stock_location_output")
        cls.stock = cls.env.ref("stock.stock_location_stock")
        cls._create_sub_locations()
        cls._create_inventory()
        cls._create_procurement()

    @classmethod
    def _create_sub_locations(cls):
        for i in range(1, 10):
            cls.env["stock.location"].create(
                {
                    "name": f"Test Location OUT {i}",
                    "barcode": f"L#OUT.{i}",
                    "location_id": cls.output.id,
                }
            )

    @classmethod
    def _create_inventory(cls):
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.product.id,
                "inventory_quantity": 50.0,
                "location_id": cls.stock.id,
            }
        )._apply_inventory()

    @classmethod
    def _create_procurement(cls):
        values = {"group_id": cls.group}
        cls.group.run(
            [
                cls.group.Procurement(
                    cls.product,
                    5.0,
                    cls.product.uom_id,
                    cls.customers,
                    "TEST",
                    "odoo tests",
                    cls.env.company,
                    values,
                )
            ]
        )

    def test_picking_suggest(self):
        self.move = self.env["stock.move"].search(
            [
                ("location_id", "=", self.stock.id),
                ("product_id", "=", self.product.id),
                ("state", "=", "assigned"),
            ]
        )
        self.assertTrue(self.move)
        self.move.move_line_ids.qty_done = 5.0
        # Put products in a particular location
        location_1 = self.env["stock.location"].search([("barcode", "=", "L#OUT.1")])
        self.move.move_line_ids.location_dest_id = location_1
        self.move._action_done()

        self.move_out = self.env["stock.move"].search(
            [("location_id", "=", self.output.id), ("product_id", "=", self.product.id)]
        )

        self.assertTrue(self.move_out)
        self.assertTrue(self.move_out.move_line_ids)

        self._create_procurement()
        self.move = self.env["stock.move"].search(
            [
                ("location_id", "=", self.stock.id),
                ("product_id", "=", self.product.id),
                ("state", "=", "assigned"),
            ]
        )
        self.assertTrue(self.move)
        self.assertEqual(
            location_1, self.move.picking_id.destination_location_suggestion_ids
        )

        # Check action
        action = self.move.picking_id.suggest_destination()
        self.assertEqual(
            "stock.picking.operation.destination.suggestion", action.get("res_model")
        )

        # Check wizard
        wizard = (
            self.env["stock.picking.operation.destination.suggestion"]
            .with_context(
                active_id=self.move.picking_id.id, active_model="stock.picking"
            )
            .create({})
        )
        self.assertEqual(self.move.picking_id, wizard.picking_id)
        self.assertEqual(location_1, wizard.destination_location_suggestion_ids)
        self.assertFalse(wizard.move_line_ids)
        self.move.move_line_ids.qty_done = 5.0
        wizard.invalidate_recordset()
        self.assertTrue(wizard.move_line_ids)
        self.assertEqual(self.move.move_line_ids, wizard.move_line_ids)

        with Form(wizard) as wizard_form:
            wizard_form.chosen_location_suggestion_id = (
                wizard.destination_location_suggestion_ids
            )

        wizard.doit()
        self.assertEqual(location_1, self.move.move_line_ids.location_dest_id)

        # Check wrong model wizard
        with self.assertRaises(ValidationError) as error:
            wizard = (
                self.env["stock.picking.operation.destination.suggestion"]
                .with_context(
                    active_id=self.move.picking_id.id, active_model="stock.picking.type"
                )
                .create({})
            )
        self.assertEqual(
            error.exception.args[0],
            "You are not launching the destination suggestion from a Stock Picking",
        )
