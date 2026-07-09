# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import _, api, models, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    omnia_mrp_orig_move = fields.Many2one("stock.move",
                                          copy=False,
                                          string="Original Move")
    def _merge_in_existing_line(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        """ This function purpose is to be override with the purpose to forbide _run_buy  method
        to merge a new po line in an existing one.
        """
        return True

    @api.model_create_multi
    def create(self, vals_list):
        analytic_id = self.env.context.get('omnia_analytic_id')
        if analytic_id:
            for vals in vals_list:
                vals.setdefault('analytic_distribution', {str(analytic_id): 100})

        order_lines = super().create(vals_list)

        for line, vals in zip(order_lines, vals_list):
            analytic_id = self.env.context.get('omnia_analytic_id')
            if analytic_id:
                line.distribution_analytic_account_ids = [(6, 0, [analytic_id])]

            orig_move_id = self.env.context.get('omnia_orig_move_id')
            if not orig_move_id:
                for command in vals.get('move_dest_ids') or []:
                    if command[0] == 4:
                        orig_move_id = command[1]
                        break
                    elif command[0] == 6 and command[2]:
                        orig_move_id = command[2][0]
                        break


            if not orig_move_id:
                continue

            line.omnia_mrp_orig_move = orig_move_id
            move = self.env['stock.move'].browse(orig_move_id)
            if not move.purchase_order_id:
                move.purchase_order_id = line.order_id.id
                move.purchase_line_id = line.id
            if not move.created_purchase_line_ids:
                move.created_purchase_line_ids = [(4, line.id)]

        return order_lines
