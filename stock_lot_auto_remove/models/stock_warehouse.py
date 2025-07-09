# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    lar_enabled = fields.Boolean(
        string="Enable Expired Lot Auto Remove",
        help="If checked, expired lots will be automatically moved to the "
        "designated destination location.",
    )

    lar_orig_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Expired Lot Origin Location",
        help="Location from which expired lots will be moved.",
    )

    lar_dest_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Expired Lot Destination Location",
        help="Location where expired lots will be moved to.",
    )

    lar_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Expired Lot Move Picking Type",
        help="Picking type used for moving expired lots.",
    )

    @api.onchange("lar_enabled")
    def _onchange_lar_enabled(self):
        """Ensure that the origin and destination locations are set when
        enabling expired lot move."""
        if self.lar_enabled:
            if not self.lar_orig_location_id:
                self.lar_orig_location_id = self.lot_stock_id
            if not self.lar_dest_location_id:
                self.lar_dest_location_id = self.wh_qc_stock_loc_id

    @api.constrains("lar_orig_location_id", "lar_dest_location_id", "lar_enabled")
    def _check_expired_lot_locations(self):
        """Ensure that:
        * the origin and destination locations are from the current warehouse,
        * the origin and destination locations are set when expired lot move is enabled,
        * the origin and destination locations are different when expired lot move is enabled.
        * the origin and destination should not be parent locations of each other.
        """
        for record in self:
            if record.lar_enabled:
                if not record.lar_orig_location_id:
                    raise ValidationError(
                        _("Please set the origin location for expired lot moves.")
                    )
                if not record.lar_dest_location_id:
                    raise ValidationError(
                        _("Please set the destination location for expired lot moves.")
                    )
                if record.lar_orig_location_id.warehouse_id != record:
                    raise ValidationError(
                        _(
                            "The origin location for expired lot moves must be from the "
                            "current warehouse."
                        )
                    )
                if record.lar_dest_location_id.warehouse_id != record:
                    raise ValidationError(
                        _(
                            "The destination location for expired lot moves must be from the "
                            "current warehouse."
                        )
                    )
                if record.lar_orig_location_id == record.lar_dest_location_id:
                    raise ValidationError(
                        _(
                            "The origin and destination locations for expired lot moves must "
                            "be different."
                        )
                    )
                orig_parent_path = record.lar_orig_location_id.parent_path
                dest_parent_path = record.lar_dest_location_id.parent_path
                if orig_parent_path != dest_parent_path:
                    if orig_parent_path.startswith(
                        dest_parent_path
                    ) or dest_parent_path.startswith(orig_parent_path):
                        raise ValidationError(
                            _(
                                "The origin and destination locations for expired lot moves "
                                "different parent locations."
                            )
                        )

    @api.constrains("lar_picking_type_id", "lar_enabled")
    def _check_lar_picking_type(self):
        """Ensure that the picking type for expired lot moves is set when
        expired lot move is enabled."""
        for record in self:
            if record.lar_enabled and not record.lar_picking_type_id:
                raise ValidationError(
                    _("Please set the picking type for expired lot moves.")
                )

    def _get_picking_type_create_values(self, max_sequence):
        """Override to set the picking type for expired lot moves."""
        create_data, max_sequence = super()._get_picking_type_create_values(
            max_sequence
        )
        max_sequence += 1
        create_data["lar_picking_type_id"] = {
            "name": _("Expired Lot Removal"),
            "code": "internal",
            "use_create_lots": False,
            "use_existing_lots": True,
            "default_location_src_id": self.lot_stock_id.id,
            "sequence": max_sequence + 3,
            "sequence_code": "LEX",
            "company_id": self.company_id.id,
        }
        return create_data, max_sequence

    @api.model
    def _cron_remove_expired_lots(self):
        """Cron job to remove expired lots."""
        warehouses = self.env["stock.warehouse"].search([("lar_enabled", "=", True)])
        for warehouse in warehouses:
            wizard = self.env["stock.lot.removal.wizard"].create(
                {
                    "warehouse_id": warehouse.id,
                }
            )
            wizard.action_run()
