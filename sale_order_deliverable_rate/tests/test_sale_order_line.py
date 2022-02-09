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
                "product_uom_qty": 0,
                "qty_delivered": 0,
            }
        ]

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

    def create_basic_so(self, array_products):
        return self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
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

    def test_no_more_to_ship(self):
        """
        Ensure that qty_to_ship is to 0 when qty_delivered == product_uom_qty
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 10)
        self.array_products[0]["product_uom_qty"] = 10
        self.array_products[0]["qty_delivered"] = 10
        so = self.create_basic_so(self.array_products[:1])

        self.assertEqual(first(so.order_line).qty_to_ship, 0)

    def test_everything_to_ship(self):
        """
        Ensure that qty_to_ship is equal to product_uom_qty
        when qty_delivered is equal to 0
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 10)
        self.array_products[0]["product_uom_qty"] = 10
        self.array_products[0]["qty_delivered"] = 0
        so = self.create_basic_so(self.array_products[:1])

        self.assertEqual(
            first(so.order_line).qty_to_ship, self.array_products[0]["product_uom_qty"]
        )

    def test_qty_to_ship(self):
        """
        Ensure that qty_to_ship is equal to product_uom_qty - qty_delivered
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 10)
        self.array_products[0]["product_uom_qty"] = 10
        self.array_products[0]["qty_delivered"] = 5
        so = self.create_basic_so(self.array_products[:1])

        self.assertEqual(
            first(so.order_line).qty_to_ship,
            self.array_products[0]["product_uom_qty"]
            - self.array_products[0]["qty_delivered"],
        )

    def test_has_delivered_more(self):
        """
        Ensure that qty_to_ship is less than 0 when a product
        is over delivered (qty_delivered is greater than product_uom_qty)
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 10)
        self.array_products[0]["product_uom_qty"] = 10
        self.array_products[0]["qty_delivered"] = 11
        so = self.create_basic_so(self.array_products[:1])

        self.assertLess(first(so.order_line).qty_to_ship, 0)

    def test_totally_deliverable(self):
        """
        Ensure that deliverable_rate is to 100%
        when product has qty_available to satisfy product_uom_qty
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 10)
        self.array_products[0]["product_uom_qty"] = 10
        self.array_products[0]["qty_delivered"] = 0
        so = self.create_basic_so(self.array_products[:1])

        self.assertEqual(first(so.order_line).deliverable_rate, 100)

    def test_partially_deliverable(self):
        """
        Ensure that deliverable_rate is to 100%
        when product has qty_available to satisfy product_uom_qty
        :return:
        """
        self._update_stock(self.array_products[0]["product"], 5)
        self.array_products[0]["product_uom_qty"] = 10
        self.array_products[0]["qty_delivered"] = 0
        so = self.create_basic_so(self.array_products[:1])

        self.assertEqual(first(so.order_line).deliverable_rate, 50)
