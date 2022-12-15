# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# Copyright 2020 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProcurementGroupCarrier(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.carrier1 = cls.env["delivery.carrier"].create(
            {
                "name": "My Test Carrier",
                "product_id": cls.env.ref("delivery.product_product_delivery").id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def test_sale_procurement_group_carrier(self):
        """Check the SO procurement group contains the carrier on SO confirmation"""
        product = self.env.ref("product.product_delivery_01")

        with Form(self.env["sale.order"]) as sale_form:
            sale_form.partner_id = self.partner
            with sale_form.order_line.new() as line_form:
                line_form.product_id = product
        sale = sale_form.save()

        wiz_action = sale.action_open_delivery_wizard()
        choose_delivery_carrier = (
            self.env[wiz_action["res_model"]]
            .with_context(**wiz_action["context"])
            .create({"carrier_id": self.carrier1.id, "order_id": sale.id})
        )
        choose_delivery_carrier.button_confirm()
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        self.assertTrue(sale.procurement_group_id.carrier_id)
        self.assertEqual(sale.procurement_group_id.carrier_id, sale.carrier_id)

        # Set SO to draft
        # Check procurement group is reset
        sale.action_draft()
        self.assertFalse(sale.procurement_group_id)
