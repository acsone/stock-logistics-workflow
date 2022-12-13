# Author: Jacques-Etienne Baudoux <je@bcim.be>
# Copyright (C) 2015-2022 BCIM <http://www.bcim.be>
#                         ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class GRNType(models.Model):
    """GRN Type"""

    _name = "stock.grn.type"
    _description = "Type of goods received note"

    name = fields.Char(string="Type", required=True)
