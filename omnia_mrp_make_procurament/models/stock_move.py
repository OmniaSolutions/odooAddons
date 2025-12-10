# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2024 https://OmniaSolutions.website
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
from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    ava_tmp_pur_order = fields.Char("Pur.Ava")
    run_a_executed = fields.Boolean("RunA Executed")

    def _action_confirm(self, merge=True, merge_into=False):
        moves = self.env['stock.move']
        for move_id in self:
            moves += move_id.with_context(omnia_mrp_orig_move=move_id)
        return super()._action_confirm(merge=merge, merge_into=merge_into)
