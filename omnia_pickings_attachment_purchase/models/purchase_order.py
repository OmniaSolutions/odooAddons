##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2010 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models
from odoo import api
from odoo import _
import json


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def attach_to_pickings(self):
        all_pickings = self.env['stock.picking']
        for order in self:
            all_pickings += order.picking_ids
        action = self.env.ref('omnia_pickings_attachment.plm_temporary_purchase_picking_attachments_action')
        result = action.read()[0]
        ctx = json.loads(result['context'])
        ctx['default_picking_ids'] = all_pickings.ids
        result['context'] = json.dumps(ctx)
        return result
