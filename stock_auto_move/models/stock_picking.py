# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        self._transfer_pickings_with_auto_move()
        return res

    @api.multi
    def _transfer_pickings_with_auto_move(self):
        """This function is meant to simulate what a user would normally
        transfer a picking from the user interface either partial processing
        or full processing.
        """
        for picking in self:
            auto_moves = self._get_auto_moves(picking)
            auto_moves_by_pickings = self._get_auto_moves_by_pickings(auto_moves)
            for auto_picking in auto_moves_by_pickings:
                if len(auto_picking.move_lines) != len(
                        auto_moves_by_pickings[auto_picking]):
                    # Create a back order for remaning moves
                    backorder_moves = \
                        auto_picking.move_lines - \
                        auto_moves_by_pickings[auto_picking]
                    self._create_backorder(
                        picking=auto_picking, backorder_moves=backorder_moves)

                # Create immediate transfer wizard so it will fill the qty_done
                # on the auto move linked operation
                auto_picking.do_prepare_partial()
                wizard = self.env['stock.immediate.transfer'].create(
                    {'pick_id': auto_picking.id})
                wizard.process()

        return

    @api.model
    def _get_auto_moves(self, picking):
        dest_moves = picking.move_lines.mapped('move_dest_id')

        return dest_moves.filtered(
            lambda m: m.state == 'assigned' and m.auto_move)

    @api.model
    def _get_auto_moves_by_pickings(self, auto_moves):
        """ Group moves by picking.
        @param auto_moves: stock.move data set
        @return dict dict of moves grouped by pickings
        {stock.picking(id): stock.move(id1, id2, id3 ...), ...}
        """
        auto_moves_by_pickings = dict()
        for move in auto_moves:
            if move.picking_id in auto_moves_by_pickings:
                auto_moves_by_pickings[move.picking_id] |= move
            else:
                auto_moves_by_pickings.update({move.picking_id: move})
        return auto_moves_by_pickings
