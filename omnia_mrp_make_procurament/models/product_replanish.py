# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2023 https://OmniaSolutions.website
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
'''
Created on 10 Nov 2023

@author: mboscolo
'''
import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class ProductReplenish(models.TransientModel):
    _inherit = 'product.replenish'


    def custom_launch_replenishment(self, name, origin):
        uom_reference = self.product_id.uom_id
        self.quantity = self.product_uom_id._compute_quantity(self.quantity, uom_reference)
        try:
            self.env['procurement.group'].with_context(clean_context(self.env.context)).run(
                self.product_id,
                self.quantity,
                uom_reference,
                self.warehouse_id.lot_stock_id, # Location
                name,
                origin,
                self._prepare_run_values() # Values
            )
        except UserError as error:
            raise UserError(error)


