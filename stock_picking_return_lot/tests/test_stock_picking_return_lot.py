# Copyright 2020 Iryna Vyshnevska Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests.common import TransactionCase


class StockPickingReturnLotTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_obj = cls.env["stock.picking"]
        partner = cls.env["res.partner"].create({"name": "Test"})
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "type": "product", "tracking": "lot"}
        )
        cls.lot_1 = cls.env["stock.lot"].create(
            {"name": "000001", "product_id": cls.product.id}
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {"name": "000002", "product_id": cls.product.id}
        )
        picking_type_out = cls.env.ref("stock.picking_type_out")
        stock_location = cls.env.ref("stock.stock_location_stock")
        customer_location = cls.env.ref("stock.stock_location_customers")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, stock_location, 1, lot_id=cls.lot_1
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, stock_location, 2, lot_id=cls.lot_2
        )
        cls.picking = cls.picking_obj.create(
            {
                "partner_id": partner.id,
                "picking_type_id": picking_type_out.id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 3,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": stock_location.id,
                            "location_dest_id": customer_location.id,
                        },
                    )
                ],
            }
        )
        cls.picking.action_confirm()
        cls.picking.action_assign()
        cls.picking.action_set_quantities_to_reservation()
        cls.picking._action_done()

    @classmethod
    def create_return_wiz(cls):
        return (
            cls.env["stock.return.picking"]
            .with_context(active_id=cls.picking.id, active_model="stock.picking")
            .create({})
        )

    def test_partial_return(self):
        wiz = self.create_return_wiz()
        wiz._onchange_picking_id()
        self.assertEqual(len(wiz.product_return_moves), 2)
        return_line_1 = wiz.product_return_moves.filtered(
            lambda m, lot=self.lot_1: m.lot_id == lot
        )
        return_line_2 = wiz.product_return_moves.filtered(
            lambda m, lot=self.lot_2: m.lot_id == lot
        )
        self.assertEqual(return_line_1.quantity, 1)
        self.assertEqual(return_line_2.quantity, 2)
        return_line_2.quantity = 1
        picking_returned_id = wiz._create_returns()[0]
        picking_returned = self.picking_obj.browse(picking_returned_id)
        move_1 = picking_returned.move_ids.filtered(
            lambda m, lot=self.lot_1: m.restrict_lot_id == lot
        )
        move_2 = picking_returned.move_ids.filtered(
            lambda m, lot=self.lot_2: m.restrict_lot_id == lot
        )
        self.assertEqual(move_1.move_line_ids.lot_id, self.lot_1)
        self.assertEqual(move_2.move_line_ids.lot_id, self.lot_2)
        self.assertEqual(move_2.product_qty, 1)

    def test_full_return_after_partial_return(self):
        self.test_partial_return()
        wiz = self.create_return_wiz()
        wiz._onchange_picking_id()
        self.assertEqual(len(wiz.product_return_moves), 2)

        return_line_1 = wiz.product_return_moves.filtered(
            lambda m, lot=self.lot_1: m.lot_id == lot
        )
        return_line_2 = wiz.product_return_moves.filtered(
            lambda m, lot=self.lot_2: m.lot_id == lot
        )
        self.assertEqual(return_line_1.quantity, 0)
        self.assertEqual(return_line_2.quantity, 1)
        picking_returned_id = wiz._create_returns()[0]
        picking_returned = self.picking_obj.browse(picking_returned_id)
        move_1 = picking_returned.move_ids.filtered(
            lambda m, lot=self.lot_1: m.restrict_lot_id == lot
        )
        move_2 = picking_returned.move_ids.filtered(
            lambda m, lot=self.lot_2: m.restrict_lot_id == lot
        )
        self.assertFalse(move_1)
        self.assertEqual(move_2.move_line_ids.lot_id, self.lot_2)
        self.assertEqual(move_2.product_qty, 1)
