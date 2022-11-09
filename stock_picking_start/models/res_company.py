# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    stock_picking_assign_operator_at_start = fields.Boolean(
        "Assign responsible on stock picking start", default=False
    )
