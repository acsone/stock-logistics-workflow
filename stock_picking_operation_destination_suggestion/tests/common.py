# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.base.tests.common import BaseCommon


class PickingDestinationSuggestCommon(BaseCommon):
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
