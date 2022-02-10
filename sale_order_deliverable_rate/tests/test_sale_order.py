# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import first
from odoo.tests import Form
from odoo.tests.common import SavepointCase


class TestSaleOrderDeliverableRate(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.WizardQty = cls.env["stock.change.product.qty"]

        cls.Partner = cls.env["res.partner"]
        cls.Product = cls.env["product.product"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.SaleOrderLine = cls.env["sale.order.line"]

        cls.partner = cls.Partner.create({"name": "Customer"})

        cls.array_products = [
            {
                "product": cls.Product.create(
                    {"name": "Test Product 1", "type": "product"}
                ),
                "product_uom_qty": 10,
                "qty_delivered": 0,
            },
            {
                "product": cls.Product.create(
                    {"name": "Test Product 2", "type": "product"}
                ),
                "product_uom_qty": 10,
                "qty_delivered": 0,
            },
            {
                "product": cls.Product.create(
                    {"name": "Test Product 3", "type": "product"}
                ),
                "product_uom_qty": 10,
                "qty_delivered": 0,
            },
        ]

        cls.so_empty = cls.create_basic_so([])
        cls.so_one_line = cls.create_basic_so(cls.array_products[:1])
        cls.so_three_line = cls.create_basic_so(cls.array_products)

    @classmethod
    def _update_stock(cls, product, qty):
        """
        Set the stock quantity of the product
        :param product: product.product recordset
        :param qty: float
        """
        wizard = Form(cls.WizardQty)
        wizard.product_id = product
        wizard.product_tmpl_id = product.product_tmpl_id
        wizard.new_quantity = qty
        wizard = wizard.save()
        wizard.change_product_qty()

    @classmethod
    def create_basic_so(cls, array_products):
        return cls.SaleOrder.create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product["product"].id,
                            "name": "line 1",
                            "product_uom_qty": product["product_uom_qty"],
                            "qty_delivered": product["qty_delivered"],
                            "price_unit": 10,
                        },
                    )
                    for product in array_products
                ],
            }
        )

    def test_totally_deliverable(self):
        """
        Ensure that deliverable_rate of an order is to 100%
        when it contains one order_line with a product who has enough stock
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 10)
        first(self.so_one_line.order_line).product_uom_qty = 10
        first(self.so_one_line.order_line).qty_delivered = 0

        self.assertEqual(self.so_one_line.deliverable_rate, 100)

    def test_partially_deliverable(self):
        """
        Ensure that deliverable_rate of an order is to 80%
        when it contains one order_line with a product who has
        stock to satisfy  order to 80%
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 8)
        first(self.so_one_line.order_line).product_uom_qty = 10
        first(self.so_one_line.order_line).qty_delivered = 0

        self.assertEqual(self.so_one_line.deliverable_rate, 80)

    def test_empty_order(self):
        """
        Ensure that deliverable_rate of an empty order is to 100%
        empty stand for an order with no order_lines
        :return:
        """
        so = self.create_basic_so([])

        self.assertEqual(self.so_empty.deliverable_rate, 100)

    def test_all_order_line_delivered(self):
        """
        Ensure that deliverable_rate of an order
        with all order_line delivered is to 100%
        :return:
        """
        first(self.so_one_line.order_line).product_uom_qty = 10
        first(self.so_one_line.order_line).qty_delivered = 10

        self.assertEqual(self.so_one_line.deliverable_rate, 100)

    def test_order_line_over_delivered(self):
        """
        Ensure that deliverable_rate of an order
        with order_line who has more qty_delivered
        than product_uom_qty is to 100%
        :return:
        """
        first(self.so_one_line.order_line).product_uom_qty = 10
        first(self.so_one_line.order_line).qty_delivered = 11

        self.assertEqual(self.so_one_line.deliverable_rate, 100)

    def test_all_product_no_stock(self):
        """
        Ensure that deliverable_rate of an order is to 0%
        when all order_line has a product that has no stock
        :return:
        """
        for product in self.array_products:
            self._update_stock(product["product"], 0)

        self.assertEqual(self.so_three_line.deliverable_rate, 0)
