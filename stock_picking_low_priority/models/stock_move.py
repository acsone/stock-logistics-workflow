# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

# The characters before "0" when sorting a list of characters would be any
# characters with a Unicode value lower than 48, which is the Unicode value for
# the character 0. This will ensure that the "Not urgent" option is always
# before the "Normal" option when sorted alphabetically by the database (and also
# python). Don't forget that a selection field into odoo is stored in a VARCHAR
# column in the database.
LOW_PRIORITY_VALUE = chr(ord("0") - 1)


class StockMove(models.Model):
    _inherit = "stock.move"

    priority = fields.Selection(
        selection_add=[(LOW_PRIORITY_VALUE, "Not urgent"), ("0",)],
        ondelete={LOW_PRIORITY_VALUE: "set default"},
    )
