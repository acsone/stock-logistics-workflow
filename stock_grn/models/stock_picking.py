# Author: Jacques-Etienne Baudoux <je@bcim.be>
# Copyright (C) 2015-2022 BCIM <http://www.bcim.be>
#                         ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    grn_id = fields.Many2one(
        comodel_name="stock.grn",
        string="Goods Received Note",
        copy=False,
        readonly=True,
    )
    grn_date = fields.Datetime(
        related="grn_id.date", string="GRN Date", store=True, index=True, readonly=True
    )
    delivery_note_supplier_number = fields.Char(
        related="grn_id.delivery_note_supplier_number",
        string="Supplier delivery note number",
        store=True,
        readonly=True,
    )
