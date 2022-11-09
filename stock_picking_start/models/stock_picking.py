# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from operator import attrgetter

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


class StockPicking(models.Model):

    _inherit = "stock.picking"

    user_id = fields.Many2one(
        "res.users",
        default=lambda self: self._default_user_id,
    )

    action_start_allowed = fields.Boolean(
        compute="_compute_action_start_allowed",
    )

    def _default_user_id(self):
        if not self.env.company.stock_picking_assign_operator_at_start:
            return self.env.user
        return False

    @api.depends("state", "printed")
    def _compute_action_start_allowed(self):
        for record in self:
            record.action_start_allowed = (
                record.state == "assigned" and not record.printed
            )

    def _check_action_start_allowed(self):
        no_start_allowed = self.filtered(lambda p: not p.action_start_allowed)
        if no_start_allowed:
            raise UserError(
                _(
                    "The following picking(s) can't be started:\n" "%(names)s",
                    names="\n".join(no_start_allowed.mapped("name")),
                )
            )

    def _prepare_action_start_values(self, company):
        value = {"printed": True}
        if company.stock_picking_assign_operator_at_start:
            value["user_id"] = self.env.uid
        return value

    def action_start(self):
        self._check_action_start_allowed()
        for company, pickings in tools.groupby(self, attrgetter("company_id")):
            # pickings is a list of picking not a recordset
            pickings = self.browse([p.id for p in pickings])
            pickings.write(self._prepare_action_start_values(company=company))
