# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2020 https://OmniaSolutions.website
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
Created on 2 Mar 2020

@author: mboscolo
'''

import datetime
from odoo import api, fields, models

class MakeProcurement(models.TransientModel):
    _inherit = 'make.procurement'

    @api.multi
    def make_procurement1(self, origin):
        """ Creates procurement order for selected product. """
        ProcurementOrder = self.env['procurement.order']
        for wizard in self:
            # we set the time to noon to avoid the date to be changed because of timezone issues
            date = fields.Datetime.from_string(wizard.date_planned)
            date = date + datetime.timedelta(hours=12)
            date = fields.Datetime.to_string(date)

            procurement = ProcurementOrder.create({
                'name': 'Manual Created from: %s' % (origin),
                'date_planned': date,
                'product_id': wizard.product_id.id,
                'product_qty': wizard.qty,
                'product_uom': wizard.uom_id.id,
                'warehouse_id': wizard.warehouse_id.id,
                'location_id': wizard.warehouse_id.lot_stock_id.id,
                'company_id': wizard.warehouse_id.company_id.id,
                'route_ids': [(6, 0, wizard.route_ids.ids)]})
            return procurement

        
            
            