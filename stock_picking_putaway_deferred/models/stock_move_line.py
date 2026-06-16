# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from __future__ import annotations

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    putaway_deferred = fields.Boolean(
        default=False,
        copy=False,
        help=(
            "Putaway strategy has not been applied for this operation. "
            "Use 'Recompute Putaways' on the picking before validating."
        ),
    )

    @api.depends(
        "picking_type_id.defer_putaway_to_operator",
        "putaway_deferred",
    )
    def _compute_can_recompute_putaways(self):
        return super()._compute_can_recompute_putaways()

    def write(self, vals):
        to_clear = self.env["stock.move.line"]
        if "location_dest_id" in vals and not self._context.get(
            "deferred_putaway_apply"
        ):
            new_loc_id = vals["location_dest_id"]
            # Operator explicitly set a *different* destination: treat it as applied.
            # Do NOT clear when the system propagates the same value (e.g. from
            # stock.package_level.write/_check_entire_pack rewriting the identical
            # location on an already-deferred line).
            to_clear = self.filtered(
                lambda l: l.putaway_deferred and l.location_dest_id.id != new_loc_id
            )
        result = super().write(vals)
        if to_clear:
            to_clear.putaway_deferred = False
        return result

    def _can_recompute_putaway(self):
        # Allow recomputation for package-level moves (whole package being
        # relocated): result_package_id == package_id in that case, and the
        # package_level_id is always set.  Only exclude lines whose
        # result_package_id represents a *new* package being filled during the
        # operation (no package_level_id), since the operator has explicitly
        # chosen that destination and it must never be overridden.
        if self.picking_type_id.defer_putaway_to_operator:
            return self.picking_id._can_recompute_putaway() and not (
                self.result_package_id and not self.package_level_id
            )
        return super()._can_recompute_putaway()

    def _apply_putaway_strategy(self):
        if not self._context.get("deferred_putaway_apply"):
            # Lines belonging to deferred picking types must not have their
            # putaway computed now (called from _action_assign). Mark them and
            # leave their location_dest_id at the move's destination.
            # Lines whose result_package_id is a *new* package being filled
            # (no package_level_id) are excluded: the operator sets that
            # destination explicitly and it cannot be recomputed.  Lines that
            # move a whole existing package (package_level_id is set) are
            # included in the deferred mechanism.
            deferred = self.filtered(
                lambda line: line.picking_type_id.defer_putaway_to_operator
                and not (line.result_package_id and not line.package_level_id)
            )
            if deferred:
                deferred.putaway_deferred = True
            return super(StockMoveLine, self - deferred)._apply_putaway_strategy()
        return super()._apply_putaway_strategy()

    def _action_done(self):
        deferred = self.filtered("putaway_deferred")
        if deferred:
            raise UserError(
                _(
                    "Putaway strategy has not been applied on the following operations:\n%s\n"
                    "Use 'Recompute Putaways' before processing.",
                    "\n".join(
                        f"- {line.product_id.display_name} -> "
                        f"{line.location_dest_id.display_name}"
                        for line in deferred
                    ),
                )
            )
        return super()._action_done()

    def _recompute_putaways(self) -> None:
        to_recompute_lines = self._filtered_for_putaway_recompute()
        # Inject context so that _apply_putaway_strategy (called inside super)
        # does not skip deferred lines this time.
        res = super(
            StockMoveLine, to_recompute_lines.with_context(deferred_putaway_apply=True)
        )._recompute_putaways()
        to_recompute_lines.putaway_deferred = False
        return res
