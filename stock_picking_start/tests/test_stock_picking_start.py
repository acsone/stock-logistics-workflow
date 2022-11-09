# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockPickinStart(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockPickinStart, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.wh = cls.env["stock.warehouse"].create(
            {
                "name": "Base Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "ship_only",
                "code": "BWH",
            }
        )
        cls.loc_stock = cls.wh.lot_stock_id
        cls.loc_customer = cls.env.ref("stock.stock_location_customers")
        cls.picking_type = cls.env.ref("stock.picking_type_out")
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "location_id": cls.loc_stock.id,
                "location_dest_id": cls.loc_customer.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "test move",
                            "product_id": cls.product.id,
                            "product_uom_qty": 5,
                            "location_id": cls.loc_stock.id,
                            "location_dest_id": cls.loc_customer.id,
                        },
                    )
                ],
            }
        )

    @classmethod
    def _update_qty_in_location(cls, location, product, quantity):
        quants = cls.env["stock.quant"]._gather(product, location, strict=True)
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        cls.env["stock.quant"]._update_available_quantity(product, location, quantity)
        cls.env["product.product"].invalidate_model(
            fnames=[
                "qty_available",
                "virtual_available",
                "incoming_qty",
                "outgoing_qty",
            ]
        )

    def test_picking_start_allowed(self):
        self.assertNotEqual(self.picking.state, "assigned")
        self.assertFalse(self.picking.action_start_allowed)
        with self.assertRaisesRegex(UserError, "can't be started"):
            self.picking.action_start()
        # makes product partially available
        self._update_qty_in_location(self.loc_stock, self.product, 3)
        self.picking.action_assign()
        self.assertEqual(self.picking.state, "assigned")
        self.assertTrue(self.picking.action_start_allowed)

        # set the picking as printed
        self.picking.printed = True
        self.assertFalse(self.picking.action_start_allowed)
        with self.assertRaisesRegex(UserError, "can't be started"):
            self.picking.action_start()

    def test_picking_start(self):
        # makes the product available
        self._update_qty_in_location(self.loc_stock, self.product, 5)
        self.picking.action_assign()
        self.assertEqual(self.picking.state, "assigned")
        self.picking.action_start()
        self.assertTrue(self.picking.printed)

    def test_picking_start_default_operator(self):
        # by default current user is proposed by default as operator
        self.assertTrue(self.picking.default_get(["user_id"]))
        # we set the company to assign operator at picking start
        self.env.user.company_id.stock_picking_assign_operator_at_start = True
        # the operator is not more proposed by default
        self.assertTrue(self.picking.default_get(["user_id"]))

    def test_picking_start_set_operator(self):
        self._update_qty_in_location(self.loc_stock, self.product, 5)
        self.picking.action_assign()
        self.assertFalse(self.picking.user_id)
        # by default the action start does not set the operator
        self.picking.action_start()
        self.assertRecordValues(self.picking, [{"user_id": False, "printed": True}])
        self.picking.printed = False
        # we set the company to assign operator at picking start
        self.env.user.company_id.stock_picking_assign_operator_at_start = True
        self.picking.action_start()
        self.assertRecordValues(
            self.picking, [{"user_id": self.env.uid, "printed": True}]
        )
