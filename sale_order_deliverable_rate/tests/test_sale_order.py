# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import first
from odoo.tests.common import SavepointCase
from ..tests.common import TestCommonSale


class TestSaleOrderDeliverableRate(TestCommonSale, SavepointCase):

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
